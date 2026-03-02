# Spec: World Map Modal in ArtistDetailScreen (Mobile)

## Goal
При клике на карточку "Страна" в ArtistDetailScreen — открывать модальное окно с картой мира (jsvectormap), на которой подсвечены страны, где артист работал.

## Data Flow

### Problem
`visited_countries` доступен только через `/api/v1/dashboard/` — это данные текущего залогиненного пользователя. Для просмотра географии *другого* артиста нужен новый endpoint.

### New API Endpoint
**`GET /api/v1/artists/{id}/geography/`**

Возвращает:
```json
{
  "visited_countries": [
    {"code": "DE", "name": "Germany", "count": 3},
    {"code": "TR", "name": "Turkey", "count": 1}
  ]
}
```

Логика — аналогична `dashboard` (строки 1638-1651 в api_views.py):
- Review.objects.filter(author=artist.user, application__isnull=False)
- Group by job.country → {code, name, count}

### Files to Change (Backend)
1. `core/api_views.py` — новый view `ArtistGeographyView`
2. `core/api_urls.py` — маршрут `artists/<int:pk>/geography/`

### Files to Change (Mobile)
3. `artconnect-mobile/app/package.json` — add `jsvectormap` dependency
4. `artconnect-mobile/app/src/api/client.js` — add `artistsApi.geography(id)`
5. `artconnect-mobile/app/src/components/WorldMapModal.jsx` — новый компонент
6. `artconnect-mobile/app/src/components/WorldMapModal.css` — стили
7. `artconnect-mobile/app/src/screens/ArtistDetailScreen.jsx` — onClick на карточку "Страна"

## Map Configuration (mirror web)
```js
new jsVectorMap({
  selector: '#world-map-mobile',
  map: 'world_merc',
  backgroundColor: 'transparent',
  zoomButtons: true,
  zoomOnScroll: false,
  regionStyle: {
    initial: { fill: 'rgba(255,255,255,0.05)', stroke: 'rgba(255,255,255,0.1)', strokeWidth: 0.5 },
    hover: { fill: 'rgba(255,255,255,0.15)', cursor: 'pointer' },
    selected: { fill: '#2563EB' },
    selectedHover: { fill: '#1d4ed8' }
  },
  selectedRegions: visitedCodes,
  onRegionTooltipShow(event, tooltip, code) { ... }
});
```

## Design
- ModalOverlay (fullscreen), dark bg
- TopBar с кнопкой "Закрыть" (X)
- Карта мира с подсвеченными странами (#2563EB)
- Под картой — список стран chips (как в ArtistDashboard)
- Tooltip при тапе на страну: имя + count

## Risk
- jsvectormap bundle ~100KB (gzip ~35KB). Допустимо для карты.
- Билд уже 527KB — добавит ~15-20% (с tree-shaking map data).
