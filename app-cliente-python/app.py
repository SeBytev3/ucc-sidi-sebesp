import psycopg2
import time
import random

DB_URL = "dbname='postgres' user='postgres' host='localhost' password='postgres'"

def main():
    print("Cliente Python 🐍  by Sebastian Espinosa B. 😎")
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    try:
        while True:
            wait_time = random.randint(1, 10)  # Espera aleatoria entre 1 y 10 segundos
            time.sleep(wait_time)

            cursor.execute("SELECT id, name FROM public.dummy")
            results = cursor.fetchall()

            for row in results:
                print(f"Resultado: {row[0]} {row[1]}")  # Ajusta el índice según tu tabla

    except Exception as e:
        print(f"Error: {e}")

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
