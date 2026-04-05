ALTER TABLE shipments
ADD COLUMN IF NOT EXISTS base_tariff DOUBLE PRECISION NOT NULL DEFAULT 0;

ALTER TABLE shipments
ADD COLUMN IF NOT EXISTS first_mile_tariff DOUBLE PRECISION NOT NULL DEFAULT 0;

ALTER TABLE shipments
ADD COLUMN IF NOT EXISTS last_mile_tariff DOUBLE PRECISION NOT NULL DEFAULT 0;

ALTER TABLE shipments
ADD COLUMN IF NOT EXISTS total_tariff DOUBLE PRECISION NOT NULL DEFAULT 0;

ALTER TABLE shipments
ADD COLUMN IF NOT EXISTS delivery_mode TEXT NOT NULL DEFAULT 'SELF_DROP_OFF';

ALTER TABLE shipments ADD COLUMN IF NOT EXISTS pickup_details JSONB;

ALTER TABLE shipments ADD COLUMN IF NOT EXISTS dropoff_details JSONB;

UPDATE shipments
SET
    base_tariff = COALESCE(NULLIF(cost, 0), base_tariff),
    total_tariff = CASE
        WHEN total_tariff = 0 THEN COALESCE(cost, 0)
        ELSE total_tariff
    END,
    delivery_mode = COALESCE(
        NULLIF(delivery_mode, ''),
        'SELF_DROP_OFF'
    );

CREATE TABLE IF NOT EXISTS external_delivery_orders (
    id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL REFERENCES shipments (id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    status TEXT NOT NULL,
    external_order_id TEXT,
    quoted_price DOUBLE PRECISION NOT NULL DEFAULT 0,
    final_price DOUBLE PRECISION,
    currency TEXT NOT NULL DEFAULT 'KZT',
    tracking_url TEXT,
    idempotency_key TEXT NOT NULL,
    request_payload TEXT,
    response_payload TEXT,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (provider, external_order_id)
);

CREATE INDEX IF NOT EXISTS idx_external_delivery_orders_shipment_id ON external_delivery_orders (shipment_id);

CREATE INDEX IF NOT EXISTS idx_external_delivery_orders_provider_external ON external_delivery_orders (provider, external_order_id);