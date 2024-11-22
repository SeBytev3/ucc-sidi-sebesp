docker compose down
docker volume rm docker-compose_postgres_ppal_data
docker volume rm docker-compose_postgres_slave_data
docker compose up --build