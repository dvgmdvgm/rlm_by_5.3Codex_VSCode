# Spec: Mobile Chat Real-Time Updates

> Date: 2026-02-28
> Origin: /anchor_plan

## Objective

Fix real-time chat in the mobile app. Currently:
1. Messages don't arrive in real-time while inside a chat
2. Chat list (MessagesScreen) never updates without manual re-navigation
3. No push notifications for new messages sent via REST API
4. WebSocket connections silently fail (auth mismatch)

---

## Architecture & Context

### Current Data Flow (Broken)

```
Mobile sends message:
  ChatScreen.handleSend() → REST POST /api/conversations/{id}/send/
    → ConversationViewSet.send() → Message.objects.create()
    → Response → local state update (sender only)
    ❌ NO WebSocket broadcast
    ❌ NO push notification to recipient
    ❌ Recipient doesn't know about the message

Recipient sees message only via:
  → 5-second polling fallback in ChatScreen (if chat is open for that conversation)
  → NO update mechanism in MessagesScreen (chat list)
```

### Root Causes

| # | Problem | Root Cause | File(s) |
|---|---------|-----------|---------|
| 1 | WS auth fails for mobile | `asgi.py` uses `AuthMiddlewareStack` (session/cookie). Mobile uses Token auth. `new WebSocket(url)` can't send `Authorization` header. WS connects → server sees AnonymousUser → `self.close()` | `config/asgi.py`, `core/consumers.py` L21-23 |
| 2 | REST `send` doesn't broadcast | `ConversationViewSet.send()` only saves to DB, no `channel_layer.group_send()`, no push | `core/api_views.py` L1030-1044 |
| 3 | MessagesScreen static | Loads once on mount, no polling, no WS subscription | `artconnect-mobile/.../MessagesScreen.jsx` L22 |
| 4 | No push for REST messages | `send_push_to_other()` only exists in `ChatConsumer`, not called from REST endpoint | `core/api_views.py` L1030-1044 |

### Key Files

**Backend:**
- `config/asgi.py` (25 lines) — ASGI config, WS middleware
- `core/consumers.py` (426 lines) — NotificationConsumer, ChatConsumer
- `core/api_views.py` (1925 lines) — ConversationViewSet.send() at L1030
- `config/settings.py` — REST_FRAMEWORK auth, CHANNEL_LAYERS

**Mobile:**
- `artconnect-mobile/app/src/screens/ChatScreen.jsx` (266 lines) — WS connect, polling, send
- `artconnect-mobile/app/src/screens/MessagesScreen.jsx` (99 lines) — chat list
- `artconnect-mobile/app/src/api/client.js` — conversationsApi

---

## Proposed Changes

### Part A: Backend — Token Auth for WebSocket

- [ ] **A1. Create `core/middleware.py` — `TokenAuthMiddleware`**
  - Accept token via query string: `ws://host/ws/chat/5/?token=abc123`
  - Look up `rest_framework.authtoken.models.Token`
  - Set `scope["user"]` to the token's user, or `AnonymousUser` if invalid
  - Wrap as `TokenAuthMiddlewareStack` (ASGI middleware)

```python
# core/middleware.py  (ADD — new class for WebSocket token auth)

from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs


@database_sync_to_async
def get_user_from_token(token_key):
    """Look up user by DRF auth token."""
    from rest_framework.authtoken.models import Token
    try:
        token = Token.objects.select_related("user").get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    """
    Custom middleware that authenticates WebSocket connections
    using a DRF Token passed as a query string parameter (?token=xxx).
    Falls back to the session user if no token is provided.
    """

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        token_key = params.get("token", [None])[0]

        if token_key:
            scope["user"] = await get_user_from_token(token_key)
        # If no token param, keep whatever AuthMiddlewareStack set (session user)

        return await super().__call__(scope, receive, send)
```

- [ ] **A2. Update `config/asgi.py`**
  - Wrap `URLRouter` with both `AuthMiddlewareStack` (session) AND `TokenAuthMiddleware` (token query)
  - Order: `AuthMiddlewareStack` → `TokenAuthMiddleware` → `URLRouter`
  - This way session auth still works for web, and token auth works for mobile

```python
# config/asgi.py — CHANGE
from core.middleware import TokenAuthMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        TokenAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

### Part B: Backend — REST `send` with Broadcast + Push

- [ ] **B1. `core/api_views.py` — `ConversationViewSet.send()`** (L1030-1044)
  - After `Message.objects.create()`, add:
    1. `channel_layer.group_send("chat_{conv.id}", ...)` — broadcast `new_message` event
    2. Push notification to the other participant (same logic as `ChatConsumer.send_push_to_other`)
    3. `chat_badge_update` via notification channel for the other user
  - Content filter check (same as ChatConsumer)
  - Daily message limit check (same as ChatConsumer)
  - Use `async_to_sync` since this is a sync DRF view

```python
@action(detail=True, methods=['post'])
def send(self, request, pk=None):
    """POST /api/conversations/{id}/send/ — send message with broadcast + push."""
    conv = self.get_object()
    text = request.data.get('text', '').strip()
    if not text:
        return Response({'error': 'empty'}, status=status.HTTP_400_BAD_REQUEST)

    # Content filter
    from core.content_filter import check_message, get_violation_message
    is_clean, violations = check_message(text)
    if not is_clean:
        return Response(
            {'error': get_violation_message(violations)},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Daily message limit for free accounts
    is_premium = False
    if request.user.role == 'artist':
        try:
            is_premium = request.user.artist_profile.check_premium()
        except Exception:
            pass
    else:
        try:
            is_premium = request.user.employer_profile.check_premium()
        except Exception:
            pass

    if not is_premium:
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        msgs_today = Message.objects.filter(
            sender=request.user,
            created_at__gte=today_start
        ).count()
        if msgs_today >= 10:
            return Response(
                {'error': str(_("Daily message limit (10) reached. Upgrade to Premium for unlimited messaging!"))},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

    msg = Message.objects.create(
        conversation=conv,
        sender=request.user,
        text=text,
    )
    conv.save()

    # Broadcast via WebSocket
    msg_data = {
        'id': msg.pk,
        'sender_id': request.user.pk,
        'sender_name': request.user.first_name or request.user.username,
        'sender_avatar': request.user.avatar.url if request.user.avatar else '',
        'text': msg.text,
        'created_at': msg.created_at.strftime('%H:%M'),
        'is_read': False,
    }

    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"chat_{conv.id}",
        {
            'type': 'chat_message',
            'message': msg_data,
        }
    )

    # Push notification to other participant
    other = conv.get_other_participant(request.user)
    if other:
        try:
            from core.push import send_push_notification
            sender_name = request.user.first_name or request.user.username
            send_push_notification(
                other,
                title=sender_name,
                body=text[:100],
                url=f'/chat/{conv.id}/',
                category='chat',
                related_id=conv.id,
            )
        except Exception:
            pass

        # Chat badge update
        unread_count = Conversation.objects.filter(
            participants=other,
            messages__is_read=False,
        ).exclude(messages__sender=other).distinct().count()

        async_to_sync(channel_layer.group_send)(
            f"notifications_{other.pk}",
            {
                'type': 'chat_badge_update',
                'unread_count': unread_count,
                'sender_name': msg_data.get('sender_name', ''),
                'message_preview': text[:80],
                'conv_id': str(conv.id),
            }
        )

    return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)
```

### Part C: Mobile — Pass Token in WebSocket URL

- [ ] **C1. `ChatScreen.jsx` — `connectWs()`** (L43-80)
  - Get the auth token from Capacitor Preferences (`getToken()` from `api/client.js`)
  - Append `?token=xxx` to the WS URL
  - This makes the WS connection authenticated
  - Note: `getToken()` is async, so `connectWs()` must be async too

```jsx
// In connectWs():
import { getToken } from '../api/client';

const connectWs = useCallback(async () => {
  try {
    const token = await getToken();
    const ws = new WebSocket(`${WS_BASE}/ws/chat/${id}/?token=${token || ''}`);
    // ... rest of handler
  } catch {}
}, [id, user?.id]);
```

### Part D: Mobile — MessagesScreen Auto-Refresh

- [ ] **D1. `MessagesScreen.jsx`** — Add polling every 10 seconds
  - Simple approach: `setInterval(loadConversations, 10000)` in `useEffect`
  - Also re-fetch on screen focus (React Router doesn't have focus events, but can use `visibilitychange` or simply keep polling)

```jsx
useEffect(() => {
  loadConversations();
  const interval = setInterval(loadConversations, 10000);
  return () => clearInterval(interval);
}, []);
```

### Part E: Mobile — Deduplicate Messages from WS + REST

- [ ] **E1. `ChatScreen.jsx` — `handleSend()`** (L150-162)
  - Currently adds the REST response message to local state
  - After fix B1, the WS broadcast will ALSO deliver this message
  - Must deduplicate: the WS handler already deduplicates by `msg.id`
  - Change `handleSend` to NOT add message locally — let WS deliver it
  - OR: keep local add but ensure WS handler deduplication works (it already does at L53-57)
  - Safest approach: keep both, rely on existing dedup logic (already implemented)

---

## Data Flow (After Fix)

```
Mobile sends message:
  ChatScreen.handleSend()
    → REST POST /api/conversations/{id}/send/
    → ConversationViewSet.send():
      1. Content filter ✓
      2. Daily limit check ✓
      3. Message.objects.create() ✓
      4. channel_layer.group_send("chat_{id}") → WS broadcast to all participants
      5. send_push_notification(other) → FCM push
      6. chat_badge_update via notifications channel
    → REST Response → local state update (immediate feedback)
    → WS delivers same message → dedup by id → no duplicate

Recipient in ChatScreen:
  → WS receives 'new_message' → instant update
  → Polling still runs as fallback (every 5s)

Recipient in MessagesScreen:
  → Polling every 10s refreshes conversation list
  → Push notification banner shows via NotificationBanner

Recipient outside app:
  → FCM push notification → tap → navigate to /messages/{conv_id}
```

---

## Verification & Tests

- [ ] Run `python manage.py check` — no errors
- [ ] Verify WS auth: connect to `ws://host/ws/chat/{id}/?token=xxx` — should authenticate
- [ ] Send message from User A in mobile → User B in same chat should see it instantly (via WS)
- [ ] Send message from User A → User B gets FCM push notification
- [ ] User on MessagesScreen sees updated last_message and unread count within 10s
- [ ] Send message from web (which uses WS `send_message` action) → still works as before
- [ ] Content filter blocks inappropriate messages via REST endpoint
- [ ] Free user daily limit enforced via REST endpoint

---

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|-----------|
| Double messages (REST + WS) | Low | Existing dedup by `msg.id` in ChatScreen WS handler |
| WS token leaked in URL | Low | Token already used in HTTP headers; WS query is standard practice (used by Socket.IO, etc.) |
| Polling load on MessagesScreen | Low | 10s interval is gentle; stops when component unmounts |
| CHANNEL_LAYERS not configured | None | Already configured with Redis in settings.py |

## Estimated Scope

- **Files changed**: 5-6 files (2 new/modified backend, 1 new middleware, 2-3 mobile)
- **Estimated size**: Large (~150-200 lines changed/added)
- **Risk**: Low-Medium — core chat functionality change, but additive
