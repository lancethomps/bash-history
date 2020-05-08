DROP TABLE IF EXISTS commands
;

CREATE TABLE commands (
  at        TIMESTAMP NOT NULL,
  host      TEXT      NOT NULL,
  pwd       TEXT      NOT NULL,
  user      TEXT      NOT NULL,
  command   TEXT      NOT NULL,
  exit_code INTEGER,
  pid       INTEGER,
  session   TEXT
)
;

CREATE INDEX commands_at ON commands (at)
;

CREATE INDEX commands_pwd ON commands (pwd)
;

CREATE INDEX commands_exit_code ON commands (exit_code)
;