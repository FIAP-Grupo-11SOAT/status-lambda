output "lambda_function_name" {
  description = "Nome da função Lambda"
  value       = aws_lambda_function.status_processor.function_name
}

output "lambda_function_arn" {
  description = "ARN da função Lambda"
  value       = aws_lambda_function.status_processor.arn
}