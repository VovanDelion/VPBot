import aiosqlite
from pathlib import Path
import os
import logging
from typing import Optional, Dict, Union

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.db_path = Path('data/restaurant.sqlite3')
        self.conn = None

    async def connect(self):
        """Устанавливаем соединение с базой данных"""
        try:
            # Создаем папку если не существует
            os.makedirs(self.db_path.parent, exist_ok=True)

            # Подключаемся к БД (файл создастся автоматически)
            self.conn = await aiosqlite.connect(self.db_path)
            logger.info(f"Подключено к БД: {self.db_path}")

            # Включаем поддержку внешних ключей
            await self.conn.execute("PRAGMA foreign_keys = ON")

            # Создаем таблицы
            await self._create_tables()
            return self
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise ConnectionError(f"Не удалось подключиться к БД: {e}")

    async def _create_tables(self):
        """Создаем таблицы в базе данных"""
        try:
            await self.conn.executescript('''
                CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS dishes (
                dish_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                category_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            );
                
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    phone TEXT,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );


                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    delivery_type TEXT NOT NULL,
                    address TEXT,
                    phone TEXT NOT NULL,
                    status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                CREATE TABLE IF NOT EXISTS order_items (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    dish_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(order_id),
                    FOREIGN KEY (dish_id) REFERENCES dishes(dish_id)
                );
                
                CREATE TABLE IF NOT EXISTS feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_id INTEGER,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            );
            
            ''')
            await self.conn.commit()
            logger.info("Таблицы успешно созданы")
        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            raise

    async def add_user(self, user_id: int, username: Optional[str], full_name: str,
                       phone: Optional[str] = None) -> bool:
        """Добавляем нового пользователя"""
        try:
            await self.conn.execute(
                "INSERT OR REPLACE INTO users (user_id, username, full_name, phone) VALUES (?, ?, ?, ?)",
                (user_id, username, full_name, phone)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя {user_id}: {e}")
            return False

    async def get_dish_categories(self):
        """Получаем все категории блюд"""
        try:
            async with self.conn.execute(
                    "SELECT category_id, name FROM categories ORDER BY name"
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения категорий блюд: {e}")
            return []

    async def get_dishes_by_category(self, category_id: int):  # Изменили тип параметра
        """Получаем блюда по категории"""
        try:
            async with self.conn.execute(
                    "SELECT dish_id, name, description, price FROM dishes WHERE category_id = ?",  # Стало
                    (category_id,)) as cursor:
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения блюд категории: {e}")
            return []

    async def get_dish_by_id(self, dish_id: int):
        """Получаем блюдо по ID"""
        try:
            async with self.conn.execute(
                    "SELECT dish_id, name, description, price, category_id FROM dishes WHERE dish_id = ?",
                    (dish_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(zip([column[0] for column in cursor.description], row))
                return None
        except Exception as e:
            logger.error(f"Ошибка получения блюда {dish_id}: {e}")
            return None

    async def add_dish(self, name: str, description: str, price: float, category_id: int):
        """Добавляем новое блюдо в меню"""
        try:
            await self.conn.execute(
                "INSERT INTO dishes (name, description, price, category_id) VALUES (?, ?, ?, ?)",
                (name, description, price, category_id)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления блюда: {e}")
            return False

    async def get_user(self, user_id: int):
        """Получаем пользователя по ID"""
        if not self.conn:
            raise ConnectionError("Соединение с БД не установлено. Вызовите connect() перед использованием.")

        try:
            async with self.conn.execute(
                    "SELECT * FROM users WHERE user_id = ?",
                    (user_id,)
            ) as cursor:
                return await cursor.fetchone()
        except Exception as e:
            logger.error(f"Ошибка при получении пользователя {user_id}: {e}")
            return None

    async def create_order(self, user_id: int, total_amount: float, delivery_type: str,
                           address: str, phone: str) -> int:
        """Создаем новый заказ и возвращаем его ID"""
        try:
            cursor = await self.conn.execute(
                "INSERT INTO orders (user_id, total_amount, delivery_type, address, phone) "
                "VALUES (?, ?, ?, ?, ?) RETURNING order_id",
                (user_id, total_amount, delivery_type, address, phone)
            )
            order_id = (await cursor.fetchone())[0]
            await self.conn.commit()
            return order_id
        except Exception as e:
            logger.error(f"Ошибка создания заказа: {e}")
            raise

    async def add_order_item(self, order_id: int, dish_id: int, quantity: int, price: float):
        """Добавляем позицию в заказ"""
        try:
            await self.conn.execute(
                "INSERT INTO order_items (order_id, dish_id, quantity, price) "
                "VALUES (?, ?, ?, ?)",
                (order_id, dish_id, quantity, price)
            )
            await self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка добавления позиции в заказ: {e}")
            raise

    async def get_user_orders(self, user_id: int):
        """Получаем список заказов пользователя"""
        try:
            async with self.conn.execute(
                    "SELECT order_id, total_amount, delivery_type, status, created_at "
                    "FROM orders WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
            ) as cursor:
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения заказов пользователя {user_id}: {e}")
            return []

    async def get_order_details(self, order_id: int):
        """Получаем детали заказа"""
        try:
            async with self.conn.execute(
                    "SELECT * FROM orders WHERE order_id = ?",
                    (order_id,)
            ) as cursor:
                order = await cursor.fetchone()

            async with self.conn.execute(
                    "SELECT d.name, oi.quantity, oi.price "
                    "FROM order_items oi "
                    "JOIN dishes d ON oi.dish_id = d.dish_id "
                    "WHERE oi.order_id = ?",
                    (order_id,)
            ) as cursor:
                items = await cursor.fetchall()

            return {'order': order, 'items': items}
        except Exception as e:
            logger.error(f"Ошибка получения деталей заказа {order_id}: {e}")
            return None

    async def add_feedback(self, user_id: int, order_id: int, rating: int, comment: Optional[str] = None) -> bool:
        """Добавляем отзыв к заказу"""
        try:
            await self.conn.execute(
                "INSERT INTO feedback (user_id, order_id, rating, comment) VALUES (?, ?, ?, ?)",
                (user_id, order_id, rating, comment)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления отзыва: {e}")
            return False

    async def get_feedback(self, order_id: int):
        """Получаем отзыв по ID заказа"""
        try:
            async with self.conn.execute(
                    "SELECT * FROM feedback WHERE order_id = ?",
                    (order_id,)
            ) as cursor:
                return await cursor.fetchone()
        except Exception as e:
            logger.error(f"Ошибка получения отзыва для заказа {order_id}: {e}")
            return None

    async def get_user_feedback(self, user_id: int):
        """Получаем все отзывы пользователя"""
        try:
            async with self.conn.execute(
                    "SELECT * FROM feedback WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
            ) as cursor:
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения отзывов пользователя {user_id}: {e}")
            return []

    async def get_admin_stats(self):
        """Получение статистики для админ-панели"""
        try:
            # Общее количество заказов
            async with self.conn.execute("SELECT COUNT(*) FROM orders") as cursor:
                total_orders = (await cursor.fetchone())[0] or 0

            # Средний чек
            async with self.conn.execute("SELECT AVG(total_amount) FROM orders") as cursor:
                avg_order = (await cursor.fetchone())[0] or 0

            # Общий доход
            async with self.conn.execute("SELECT SUM(total_amount) FROM orders") as cursor:
                total_revenue = (await cursor.fetchone())[0] or 0

            # Последние 5 заказов
            recent_orders = await self.get_recent_orders(5)

            return {
                'total_orders': total_orders,
                'avg_order': round(avg_order, 2),
                'total_revenue': round(total_revenue, 2),
                'recent_orders': "\n".join(
                    f"#{o['order_id']} - {o['total_amount']} руб. - {o['status']}"
                    for o in recent_orders
                )
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {
                'total_orders': 0,
                'avg_order': 0,
                'total_revenue': 0,
                'recent_orders': "Нет данных"
            }

    async def get_recent_orders(self, limit: int = 5):
        """Получение последних заказов"""
        try:
            async with self.conn.execute(
                    "SELECT order_id, total_amount, status FROM orders ORDER BY created_at DESC LIMIT ?",
                    (limit,)
            ) as cursor:
                return [dict(row) for row in await cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения последних заказов: {e}")
            return []

    async def get_all_dishes(self):
        """Получение всех блюд для управления меню"""
        try:
            async with self.conn.execute(
                    "SELECT d.dish_id, d.name, d.price, c.name as category_name "
                    "FROM dishes d "
                    "LEFT JOIN categories c ON d.category_id = c.category_id "
                    "ORDER BY c.name, d.name"
            ) as cursor:
                rows = await cursor.fetchall()
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения списка блюд: {e}")
            return []

    async def update_dish(self, dish_id: int, **kwargs):
        """Обновление информации о блюде"""
        try:
            if not kwargs:
                return True

            set_clause = ", ".join(f"{key} = ?" for key in kwargs.keys())
            values = list(kwargs.values())
            values.append(dish_id)

            query = f"UPDATE dishes SET {set_clause} WHERE dish_id = ?"

            await self.conn.execute(query, values)
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления блюда {dish_id}: {e}")
            return False

    async def delete_dish(self, dish_id: int) -> bool:
        """Удаление блюда из меню"""
        try:
            await self.conn.execute(
                "DELETE FROM dishes WHERE dish_id = ?",
                (dish_id,)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления блюда {dish_id}: {e}")
            return False

    async def get_all_users(self):
        """Получение списка всех пользователей"""
        try:
            async with self.conn.execute(
                    "SELECT user_id, username, full_name, phone, registration_date FROM users ORDER BY registration_date DESC"
            ) as cursor:
                return [dict(row) for row in await cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка получения списка пользователей: {e}")
            return []

    async def update_order_status(self, order_id: int, status: str) -> bool:
        """Обновление статуса заказа"""
        try:
            await self.conn.execute(
                "UPDATE orders SET status = ? WHERE order_id = ?",
                (status, order_id)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления статуса заказа {order_id}: {e}")
            return False

    async def create_cart_tables(self):
        """Создаем таблицы для корзины"""
        try:
            await self.conn.executescript('''
                CREATE TABLE IF NOT EXISTS cart (
                    cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    dish_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (dish_id) REFERENCES dishes(dish_id)
                );

                CREATE TABLE IF NOT EXISTS cart_items (
                    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cart_id INTEGER NOT NULL,
                    dish_id INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    FOREIGN KEY (cart_id) REFERENCES cart(cart_id),
                    FOREIGN KEY (dish_id) REFERENCES dishes(dish_id)
                );
            ''')
            await self.conn.commit()
            logger.info("Таблицы корзины созданы")
        except Exception as e:
            logger.error(f"Ошибка создания таблиц корзины: {e}")
            raise

    async def get_cart_items(self, user_id: int):
        """Получаем содержимое корзины пользователя"""
        try:
            async with self.conn.execute('''
                SELECT c.cart_id, d.name, c.quantity, d.price 
                FROM cart c
                JOIN dishes d ON c.dish_id = d.dish_id
                WHERE c.user_id = ?
            ''', (user_id,)) as cursor:
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения корзины для пользователя {user_id}: {e}")
            return []

    async def add_to_cart(self, user_id: int, dish_id: int, quantity: int = 1) -> bool:
        """Добавляем блюдо в корзину"""
        try:
            # Проверяем, есть ли уже такое блюдо в корзине
            async with self.conn.execute(
                    "SELECT cart_id, quantity FROM cart WHERE user_id = ? AND dish_id = ?",
                    (user_id, dish_id)
            ) as cursor:
                existing = await cursor.fetchone()

            if existing:
                # Обновляем количество, если блюдо уже в корзине
                new_quantity = existing[1] + quantity
                await self.conn.execute(
                    "UPDATE cart SET quantity = ? WHERE cart_id = ?",
                    (new_quantity, existing[0]))
            else:
                # Добавляем новую запись
                await self.conn.execute(
                    "INSERT INTO cart (user_id, dish_id, quantity) VALUES (?, ?, ?)", (user_id, dish_id, quantity))

                await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления в корзину: {e}")
            return False

    async def remove_from_cart(self, user_id: int, cart_item_id: int) -> bool:
        """Удаляем позицию из корзины"""
        try:
            await self.conn.execute(
                "DELETE FROM cart WHERE cart_id = ? AND user_id = ?",
                (cart_item_id, user_id))
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления из корзины: {e}")
            return False

    async def clear_cart(self, user_id: int) -> bool:
        """Очищаем корзину пользователя"""
        try:
            await self.conn.execute(
                "DELETE FROM cart WHERE user_id = ?",
                (user_id,))
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки корзины: {e}")
            return False

    async def close(self):
        """Закрываем соединение с базой данных"""
        if self.conn:
            await self.conn.close()
            self.conn = None
            logger.info("Соединение с БД закрыто")

    async def add_category(self, name: str) -> bool:
        """Добавляем новую категорию"""
        try:
            await self.conn.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                (name,)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления категории: {e}")
            return False

    async def get_all_categories(self):
        """Получаем все категории"""
        try:
            async with self.conn.execute(
                    "SELECT * FROM categories ORDER BY name"
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения категорий: {e}")
            return []

    async def delete_category(self, category_id: int) -> bool:
        """Удаляем категорию"""
        try:
            await self.conn.execute(
                "DELETE FROM categories WHERE category_id = ?",
                (category_id,)
            )
            await self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления категории: {e}")
            return False

    async def get_category(self, category_id: int):
        """Получаем категорию по ID"""
        try:
            async with self.conn.execute(
                    "SELECT * FROM categories WHERE category_id = ?",
                    (category_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(zip([column[0] for column in cursor.description], row))
                return None
        except Exception as e:
            logger.error(f"Ошибка получения категории {category_id}: {e}")
            return None

    async def get_all_feedback(self):
        """Получение всех отзывов"""
        try:
            async with self.conn.execute('''
                SELECT f.*, u.username, u.full_name 
                FROM feedback f
                LEFT JOIN users u ON f.user_id = u.user_id
                ORDER BY f.created_at DESC
            ''') as cursor:
                rows = await cursor.fetchall()
                return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения отзывов: {e}")
            return []