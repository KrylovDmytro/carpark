import psycopg2

class DatabaseClient:
    def __init__(self):
        self.connection = psycopg2.connect(
            host="127.0.0.1",
            database="db_carpark",
            user="postgres",
            password="qwerty123"
        )
        self.cursor = self.connection.cursor()

    def fetch_active_services(self):
        self.cursor.execute("SELECT id_service, name, description, price FROM service WHERE active = TRUE")
        return self.cursor.fetchall()

    def fetch_all_services(self):
        self.cursor.execute("SELECT id_service, name FROM service")
        return self.cursor.fetchall()

    def add_service(self, name, description, price, active=True):
        query = """
        INSERT INTO service (name, description, price, active)
        VALUES (%s, %s, %s, %s)
        RETURNING id_service;
        """
        self.cursor.execute(query, (name, description, price, active))
        id_service = self.cursor.fetchone()[0]
        self.connection.commit()
        return id_service

    def update_service(self, service_id, name, description, active):
        query = """
        UPDATE service
        SET name = %s, description = %s, active = %s
        WHERE id_service = %s;
        """
        self.cursor.execute(query, (name, description, active, service_id))
        self.connection.commit()

    def add_client(self, name, numbercar, brand, payment_card, chat_id):
        try:
            # Спочатку додаємо клієнта
            self.cursor.execute("""
            INSERT INTO clients (name_client, numbercar_client, brand, payment_card)
            VALUES (%s, %s, %s, %s) RETURNING id_client;
            """, (name, numbercar, brand, payment_card))
            id_client = self.cursor.fetchone()[0]

            # Перевірка наявності запису в telegram_info
            self.cursor.execute("""
            SELECT chat_id FROM telegram_info WHERE chat_id = %s;
            """, (chat_id,))
            result = self.cursor.fetchone()

            if result:
                # Якщо запис існує, оновлюємо його
                self.cursor.execute("""
                UPDATE telegram_info SET id_client = %s WHERE chat_id = %s;
                """, (id_client, chat_id))
            else:
                # Якщо запису немає, додаємо новий
                self.cursor.execute("""
                INSERT INTO telegram_info (chat_id, id_client)
                VALUES (%s, %s);
                """, (chat_id, id_client))
            
            self.connection.commit()
            return id_client, "Клієнта додано успішно."
        except Exception as e:
            self.connection.rollback()
            return None, f"Помилка: {e}"

    def authenticate_by_numbercar(self, numbercar):
        try:
            self.cursor.execute("""
            SELECT c.id_client, c.name_client, c.numbercar_client, c.brand, c.payment_card,
            to_char(i.entry_date, 'YYYY-MM-DD HH24:MI:SS') as entry_date,
            to_char(i.exit_date, 'YYYY-MM-DD HH24:MI:SS') as exit_date,
            ps.place_number, ps.floor
            FROM clients c
            JOIN info i ON c.numbercar_client = i.nubercar_id
            LEFT JOIN parking_spaces ps ON c.id_client = ps.id_client
            WHERE c.numbercar_client = %s;
            """, (numbercar,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"Помилка виконання запиту: {e}")
            return None

    def get_client_by_id(self, id_client):
        try:
            self.cursor.execute("SELECT id_client, name_client, numbercar_client, brand, payment_card FROM clients WHERE id_client = %s;", (id_client,))
            result = self.cursor.fetchone()
            if result:
                print(f"get_client_by_id: {result}")
                return result
            else:
                print("get_client_by_id: Клієнта не знайдено")
                return None
        except Exception as e:
            return f"Помилка: {e}"

    def create_order(self, id_client, id_service):
        try:
            # Перевірка наявності id_client в таблиці clients
            self.cursor.execute("SELECT id_client FROM clients WHERE id_client = %s;", (id_client,))
            result = self.cursor.fetchone()
            if not result:
                print(f"create_order: Клієнт з id {id_client} не існує")
                return f"Помилка: Клієнт з id {id_client} не існує."

            query_orders = """
            INSERT INTO orders (id_client, id_service, status)
            VALUES (%s, %s, 'pending')
            RETURNING id_order;
            """
            self.cursor.execute(query_orders, (id_client, id_service))
            order_id = self.cursor.fetchone()[0]
            self.connection.commit()
            print(f"create_order: order_id = {order_id}")
            return order_id
        except Exception as e:
            self.connection.rollback()
            print(f"create_order: Помилка: {e}")
            return f"Помилка: {e}"

    def update_order_status(self, id_order, status):
        try:
            query = """
            UPDATE orders
            SET status = %s
            WHERE id_order = %s;
            """
            self.cursor.execute(query, (status, id_order))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            return f"Помилка: {e}"

    def get_balance(self, payment_card):
        try:
            self.cursor.execute("""
            SELECT money_card
            FROM payment_methods
            WHERE number_card = %s;
            """, (payment_card,))
            return self.cursor.fetchone()[0]
        except Exception as e:
            print(f"Помилка виконання запиту: {e}")
            return None

    def deduct_money(self, payment_card, amount):
        try:
            self.cursor.execute("""
            SELECT money_card
            FROM payment_methods
            WHERE number_card = %s;
            """, (payment_card,))
            current_balance = self.cursor.fetchone()[0]

            if current_balance < amount:
                return False, current_balance

            self.cursor.execute("""
            UPDATE payment_methods
            SET money_card = money_card - %s
            WHERE number_card = %s
            RETURNING money_card;
            """, (amount, payment_card))
            new_balance = self.cursor.fetchone()[0]
            self.connection.commit()
            return True, new_balance
        except Exception as e:
            self.connection.rollback()
            print(f"Помилка: {e}")
            return False, None
        
    def extend_parking(self, numbercar):
        try:
            self.cursor.execute("""
            UPDATE info
            SET exit_date = exit_date + INTERVAL '24 hours'
            WHERE nubercar_id = %s;
            """, (numbercar,))
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            print(f"Помилка: {e}")

    def delete_user_by_numbercar(self, numbercar):
        try:
            self.cursor.execute("""
            SELECT c.id_client, t.chat_id
            FROM clients c
            LEFT JOIN telegram_info t ON c.id_client = t.id_client
            WHERE c.numbercar_client = %s;
            """, (numbercar,))
            result = self.cursor.fetchone()
            
            if result:
                id_client, chat_id = result
                
                self.cursor.execute("DELETE FROM clients WHERE id_client = %s", (id_client,))
                self.cursor.execute("DELETE FROM parking_spaces WHERE id_client = %s", (id_client,))
                
                self.connection.commit()
                return chat_id, f"Користувач з номером транспорту {numbercar} був видалений."
            else:
                return None, f"Користувач з номером транспорту {numbercar} не знайдений."
        except Exception as e:
            self.connection.rollback()
            return None, f"Помилка: {e}"

    def change_parking_space(self, id_client, place_number, floor):
        try:
            self.cursor.execute("""
            UPDATE parking_spaces
            SET place_number = %s, floor = %s
            WHERE id_client = %s;
            """, (place_number, floor, id_client))
            self.connection.commit()
            return f"Місце паркування для клієнта {id_client} змінено на місце {place_number} на поверсі {floor}."
        except Exception as e:
            self.connection.rollback()
            return f"Помилка: {e}"

    def get_order_history_by_numbercar(self, numbercar):
        try:
            query = """
            SELECT o.id_order, s.name, o.status, s.price
            FROM orders o
            JOIN service s ON o.id_service = s.id_service
            JOIN clients c ON o.id_client = c.id_client
            WHERE c.numbercar_client = %s;
            """
            self.cursor.execute(query, (numbercar,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Помилка виконання запиту: {e}")
            return []

    def fetch_client_id_by_parking_id(self, parking_id):
        try:
            self.cursor.execute("""
            SELECT id_client FROM parking_spaces WHERE id = %s;
            """, (parking_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Помилка виконання запиту: {e}")
            return None

    def close(self):
        self.cursor.close()
        self.connection.close()
