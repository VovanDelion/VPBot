from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    dishes = relationship("Dish", back_populates="category")


class Dish(Base):
    __tablename__ = "dishes"

    dish_id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text)
    price = Column(Float)
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    category = relationship("Category", back_populates="dishes")


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String(255))
    full_name = Column(String(255))
    phone = Column(String(20))
    registration_date = Column(DateTime, default=datetime.utcnow)
    profile_photo = Column(Text)
    orders = relationship("Order", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    total_amount = Column(Float)
    delivery_type = Column(String(50))
    address = Column(Text)
    phone = Column(String(20))
    status = Column(String(20), default="new")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    feedback = relationship("Feedback", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    item_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    dish_id = Column(Integer, ForeignKey("dishes.dish_id"))
    quantity = Column(Integer)
    price = Column(Float)
    order = relationship("Order", back_populates="items")
    dish = relationship("Dish")


class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=True)
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="feedbacks")
    order = relationship("Order", back_populates="feedback")


class Cart(Base):
    __tablename__ = "cart"

    cart_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    dish_id = Column(Integer, ForeignKey("dishes.dish_id"))
    quantity = Column(Integer, default=1)
    added_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")
    dish = relationship("Dish")
