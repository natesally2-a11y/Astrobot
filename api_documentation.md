# Mini App API Documentation

Base URL: `/api`

## GET /api/users/{telegram_id}
Returns the public profile and subscription metadata.

## GET /api/chart/{telegram_id}
Returns saved birth data, computed chart summary, and SVG markup.

## GET /api/readings/{telegram_id}?limit=10
Returns latest generated readings.

## POST /api/compatibility
Computes compatibility between a saved user chart and partner birth data.
