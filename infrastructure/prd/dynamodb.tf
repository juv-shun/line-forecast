resource "aws_dynamodb_table" "forecast_users" {
  "name" = "forecast_users"

  attribute {
    name = "id"
    type = "S"
  }

  "hash_key"       = "id"
  "read_capacity"  = 5
  "write_capacity" = 5
  "stream_enabled" = true
}
