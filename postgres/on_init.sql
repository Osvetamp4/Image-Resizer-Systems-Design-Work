CREATE TABLE IF NOT EXISTS task_results (
  id BIGSERIAL PRIMARY KEY,
  task_id BIGINT UNIQUE NOT NULL,
  image_url TEXT NOT NULL,
  width INT NOT NULL,
  height INT NOT NULL,
  timestamp_completed TIMESTAMP NOT NULL,
  timestamp_queued TIMESTAMP NOT NULL
);