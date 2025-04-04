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
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    phone TEXT,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS dishes (
                    dish_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL,
                    category TEXT
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
                    "SELECT DISTINCT category FROM dishes WHERE category IS NOT NULL"
            ) as cursor:
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения категорий блюд: {e}")
            return []

    async def get_dishes_by_category(self, category: str):
        """Получаем блюда по категории"""
        try:
            async with self.conn.execute(
                    "SELECT dish_id, name, description, price FROM dishes WHERE category = ?",
                    (category,)
            ) as cursor:
                return await cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения блюд категории {category}: {e}")
            return []

    async def get_dish_by_id(self, dish_id: int):
        """Получаем блюдо по ID"""
        try:
            async with self.conn.execute(
                    "SELECT dish_id, name, description, price FROM dishes WHERE dish_id = ?",
                    (dish_id,)
            ) as cursor:
                return await cursor.fetchone()
        except Exception as e:
            logger.error(f"Ошибка получения блюда {dish_id}: {e}")
            return None

    async def add_dish(self, name: str, description: str, price: float, category: str):
        """Добавляем новое блюдо в меню"""
        try:
            await self.conn.execute(
                "INSERT INTO dishes (name, description, price, category) VALUES (?, ?, ?, ?)",
                (name, description, price, category)
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