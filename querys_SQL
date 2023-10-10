SELECT TIME,
       CASE
           WHEN LENGTH(SUBSTRING(ENCODE(DATA::BYTEA, 'hex'), 2)) > 0 THEN
               (LEFT(SUBSTR(ENCODE(DATA::BYTEA, 'hex'), 3), 11)::NUMERIC / 1000000000.0)
           ELSE
               0.0 -- Default value when the data is empty or invalid
       END AS latitude,
       CASE
           WHEN LENGTH(RIGHT(SUBSTR(ENCODE(DATA::BYTEA, 'hex'), 13), 10)) > 0 THEN
               (RIGHT(SUBSTR(ENCODE(DATA::BYTEA, 'hex'), 13), 10)::NUMERIC / -1000000.0)
           ELSE
               0.0 -- Default value when the data is empty or invalid
       END AS longitude,
       CASE
           WHEN LENGTH(SUBSTRING(ENCODE(DATA::BYTEA, 'hex'), 1, 2)) > 0 THEN
               SUBSTRING(ENCODE(DATA::BYTEA, 'hex'), 1, 2)::INT
           ELSE
               0 -- Default value when the data is empty or invalid
       END AS DR,
       (tx_info->'frequency')::INT AS frequency,
       (tx_info->'modulation'->'lora'->>'spreadingFactor')::INT AS spreading_factor,
       (tx_info->'modulation'->'lora'->>'bandwidth')::INT AS bandwidth,
       (tx_info->'modulation'->'lora'->>'codeRate') AS codeRate,
       (rx_info->0->>'snr')::NUMERIC(10, 6) AS snr,
       (rx_info->0->>'rssi')::INT AS rssi,
       (rx_info->0->>'channel')::INT AS channel,
       (rx_info->0->>'gatewayId') AS gateway_id
FROM event_up
WHERE device_name='lostikRbpi'
ORDER BY TIME DESC;
