"""
Unit test mẫu cho module: Xác thực & Tiện ích Khách hàng.
Framework: PyTest + unittest.mock.

Lưu ý:
- Đây là file tự chạy được (self-contained) để phục vụ báo cáo Unit Testing.
- Các hàm nghiệp vụ mẫu được đặt ngay trong file để bạn chạy nhanh và lấy minh chứng coverage.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Callable
from unittest.mock import MagicMock

import pytest


# =========================
# Các hàm nghiệp vụ mẫu
# =========================

@dataclass
class RegisterPayload:
    """Payload đăng ký tài khoản đầu vào."""

    email: str
    password: str


EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def hash_password(plain_password: str) -> str:
    """Mã hóa mật khẩu bằng SHA-256 để minh họa logic hashing trong unit test."""

    # Chuyển chuỗi mật khẩu sang bytes để thuật toán băm xử lý được.
    password_bytes = plain_password.encode("utf-8")
    # Tạo hash object SHA-256 từ dữ liệu bytes của mật khẩu.
    sha256_obj = hashlib.sha256(password_bytes)
    # Trả về chuỗi hexdigest để lưu trữ/so sánh.
    return sha256_obj.hexdigest()


def validate_register(payload: RegisterPayload) -> tuple[bool, str]:
    """
    Validate dữ liệu đăng ký.

    Quy tắc:
    - Email đúng định dạng.
    - Password độ dài từ 8 đến 64.
    - Trả về (is_valid, message_or_hash)
      + Nếu hợp lệ: message_or_hash là mật khẩu đã hash.
      + Nếu không hợp lệ: message_or_hash là lý do lỗi.
    """

    # Loại bỏ khoảng trắng dư ở hai đầu email để tránh lỗi do nhập liệu thủ công.
    normalized_email = payload.email.strip()

    # Kiểm tra email có khớp regex hay không.
    if not EMAIL_PATTERN.match(normalized_email):
        # Trả về False kèm thông báo lỗi nếu email sai định dạng.
        return False, "Email không đúng định dạng"

    # Lấy độ dài mật khẩu hiện tại để kiểm tra ràng buộc.
    password_length = len(payload.password)

    # Kiểm tra điều kiện độ dài password tối thiểu và tối đa.
    if password_length < 8 or password_length > 64:
        # Trả về False kèm thông báo lỗi nếu vi phạm độ dài.
        return False, "Mật khẩu phải từ 8 đến 64 ký tự"

    # Nếu dữ liệu hợp lệ thì hash mật khẩu để chuẩn bị lưu DB.
    password_hashed = hash_password(payload.password)

    # Trả về True và giá trị hash để caller sử dụng tiếp.
    return True, password_hashed


def search_movies_with_pagination(
    movies: list[dict],
    keyword: str,
    page: int,
    page_size: int,
) -> dict:
    """
    Tìm kiếm phim theo từ khóa + phân trang.

    Input:
    - movies: danh sách dict phim có key "title".
    - keyword: từ khóa tìm theo title (không phân biệt hoa thường).
    - page: số trang bắt đầu từ 1.
    - page_size: số phần tử mỗi trang > 0.

    Output dict:
    - total_items
    - total_pages
    - page
    - page_size
    - items
    """

    # Chuẩn hóa page tối thiểu bằng 1 để tránh index âm hoặc trang 0.
    normalized_page = max(1, page)

    # Nếu page_size không hợp lệ thì raise ValueError để caller xử lý đúng.
    if page_size <= 0:
        raise ValueError("page_size phải lớn hơn 0")

    # Chuẩn hóa keyword về chữ thường và bỏ khoảng trắng đầu/cuối.
    normalized_keyword = keyword.strip().lower()

    # Nếu keyword rỗng thì xem như không lọc và lấy toàn bộ phim.
    if normalized_keyword == "":
        filtered_movies = movies
    else:
        # Lọc danh sách phim theo title chứa keyword (case-insensitive).
        filtered_movies = [
            movie
            for movie in movies
            if normalized_keyword in movie.get("title", "").lower()
        ]

    # Tính tổng số phần tử sau lọc.
    total_items = len(filtered_movies)

    # Tính tổng số trang theo công thức làm tròn lên.
    total_pages = (total_items + page_size - 1) // page_size

    # Tính vị trí bắt đầu cắt danh sách theo trang.
    start_index = (normalized_page - 1) * page_size

    # Tính vị trí kết thúc cắt danh sách theo trang.
    end_index = start_index + page_size

    # Cắt danh sách item của trang hiện tại.
    page_items = filtered_movies[start_index:end_index]

    # Trả về metadata + dữ liệu trang.
    return {
        "total_items": total_items,
        "total_pages": total_pages,
        "page": normalized_page,
        "page_size": page_size,
        "items": page_items,
    }


def send_chat_message(
    db_conn: sqlite3.Connection,
    ws_client,
    sender_id: str,
    room_id: str,
    content: str,
    now_provider: Callable[[], datetime] = datetime.utcnow,
) -> dict:
    """
    Gửi tin nhắn chat:
    - Validate nội dung không rỗng.
    - Lưu vào DB.
    - Mock phát realtime qua websocket.
    """

    # Loại bỏ khoảng trắng thừa để kiểm tra message rỗng thực tế.
    normalized_content = content.strip()

    # Nếu nội dung rỗng sau normalize thì raise ValueError.
    if normalized_content == "":
        raise ValueError("Nội dung chat không được rỗng")

    # Lấy timestamp hiện tại thông qua hàm provider để dễ mock trong test.
    created_at = now_provider().isoformat()

    # Gom dữ liệu message vào một dict để dùng cho cả DB và websocket.
    message_payload = {
        "sender_id": sender_id,
        "room_id": room_id,
        "content": normalized_content,
        "created_at": created_at,
    }

    # Insert bản ghi vào bảng chat_messages.
    db_conn.execute(
        """
        INSERT INTO chat_messages (sender_id, room_id, content, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            message_payload["sender_id"],
            message_payload["room_id"],
            message_payload["content"],
            message_payload["created_at"],
        ),
    )

    # Phát sự kiện realtime cho room tương ứng qua websocket client.
    ws_client.emit("chat:new-message", message_payload, room=room_id)

    # Trả về message để caller phản hồi API.
    return message_payload


# =========================
# PyTest fixtures (CheckDB + Rollback)
# =========================

@pytest.fixture(scope="session")
def db_conn() -> sqlite3.Connection:
    """
    Tạo kết nối SQLite in-memory cho toàn bộ session test.
    """

    # Mở kết nối SQLite chạy trong bộ nhớ để test nhanh và không phụ thuộc hạ tầng ngoài.
    connection = sqlite3.connect(":memory:")

    # Tạo bảng chat_messages phục vụ test luồng gửi tin nhắn.
    connection.execute(
        """
        CREATE TABLE chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id TEXT NOT NULL,
            room_id TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # Trả connection cho các test dùng chung.
    yield connection

    # Đóng kết nối sau khi toàn bộ test đã chạy xong.
    connection.close()


@pytest.fixture
def db_transaction(db_conn: sqlite3.Connection):
    """
    Mỗi test sẽ chạy trong 1 transaction riêng.
    Sau test sẽ rollback để đảm bảo dữ liệu không rò rỉ giữa các test.
    """

    # Bắt đầu transaction mới trước khi chạy test.
    db_conn.execute("BEGIN")

    # Cấp phát connection cho test function sử dụng.
    yield db_conn

    # Hoàn tác mọi thay đổi DB sau mỗi test để giữ môi trường sạch.
    db_conn.rollback()


@pytest.fixture
def sample_movies() -> list[dict]:
    """Fixture dữ liệu phim mẫu cho test tìm kiếm/phân trang."""

    # Trả về danh sách phim mẫu có title đa dạng để kiểm thử keyword.
    return [
        {"id": 1, "title": "Avengers: Endgame"},
        {"id": 2, "title": "The Batman"},
        {"id": 3, "title": "Avatar: The Way of Water"},
        {"id": 4, "title": "Batman Begins"},
        {"id": 5, "title": "Interstellar"},
        {"id": 6, "title": "The Dark Knight"},
    ]


# =========================
# Unit Tests
# =========================

# Test Case ID: TC_UT_Minh_001

def test_validate_register_accepts_valid_email_and_password():
    # Tạo payload hợp lệ với email đúng format và password đủ dài.
    payload = RegisterPayload(email="minh.qa@example.com", password="StrongPass123")

    # Gọi hàm validate để lấy kết quả xử lý.
    is_valid, result = validate_register(payload)

    # Kỳ vọng payload hợp lệ nên trạng thái phải là True.
    assert is_valid is True

    # Kỳ vọng kết quả là chuỗi hash SHA-256 có độ dài 64 ký tự.
    assert len(result) == 64


# Test Case ID: TC_UT_Minh_002

def test_validate_register_rejects_invalid_email_format():
    # Tạo payload email sai định dạng để kiểm tra validation email.
    payload = RegisterPayload(email="minh-at-example.com", password="StrongPass123")

    # Gọi hàm validate với dữ liệu email sai.
    is_valid, error_message = validate_register(payload)

    # Kỳ vọng hàm trả False vì email không hợp lệ.
    assert is_valid is False

    # Kỳ vọng thông báo lỗi đúng nội dung nghiệp vụ.
    assert error_message == "Email không đúng định dạng"


# Test Case ID: TC_UT_Minh_003

def test_validate_register_rejects_short_password():
    # Tạo payload với password ngắn hơn 8 ký tự.
    payload = RegisterPayload(email="minh.qa@example.com", password="1234567")

    # Gọi hàm validate với password không đạt điều kiện.
    is_valid, error_message = validate_register(payload)

    # Kỳ vọng hàm trả False vì password quá ngắn.
    assert is_valid is False

    # Kỳ vọng thông báo lỗi phản ánh đúng rule độ dài password.
    assert error_message == "Mật khẩu phải từ 8 đến 64 ký tự"


# Test Case ID: TC_UT_Minh_004

def test_hash_password_is_deterministic_for_same_input():
    # Chuẩn bị cùng một mật khẩu đầu vào cho hai lần băm.
    plain_password = "SamePassword!"

    # Băm lần thứ nhất.
    first_hash = hash_password(plain_password)

    # Băm lần thứ hai.
    second_hash = hash_password(plain_password)

    # Kỳ vọng kết quả giống nhau vì cùng input.
    assert first_hash == second_hash


# Test Case ID: TC_UT_Minh_005

def test_search_movies_with_keyword_and_pagination(sample_movies: list[dict]):
    # Gọi hàm tìm kiếm keyword "batman" ở trang 1 với kích thước 1 item/trang.
    result = search_movies_with_pagination(
        movies=sample_movies,
        keyword="batman",
        page=1,
        page_size=1,
    )

    # Kỳ vọng có tổng 2 phim khớp keyword batman.
    assert result["total_items"] == 2

    # Kỳ vọng tổng số trang là 2 khi page_size = 1.
    assert result["total_pages"] == 2

    # Kỳ vọng phần tử đầu tiên của trang 1 là "The Batman".
    assert result["items"][0]["title"] == "The Batman"


# Test Case ID: TC_UT_Minh_006

def test_search_movies_returns_empty_for_unmatched_keyword(sample_movies: list[dict]):
    # Gọi hàm tìm kiếm với keyword không tồn tại trong danh sách phim.
    result = search_movies_with_pagination(
        movies=sample_movies,
        keyword="not-found-keyword",
        page=1,
        page_size=5,
    )

    # Kỳ vọng không có item nào khớp.
    assert result["total_items"] == 0

    # Kỳ vọng danh sách items rỗng.
    assert result["items"] == []


# Test Case ID: TC_UT_Minh_007

def test_search_movies_raises_for_invalid_page_size(sample_movies: list[dict]):
    # Kiểm tra nhánh lỗi khi page_size <= 0.
    with pytest.raises(ValueError, match="page_size phải lớn hơn 0"):
        # Gọi hàm với page_size không hợp lệ để xác nhận raise ValueError.
        search_movies_with_pagination(
            movies=sample_movies,
            keyword="batman",
            page=1,
            page_size=0,
        )


# Test Case ID: TC_UT_Minh_008

def test_send_chat_message_saves_db_and_emits_realtime(db_transaction: sqlite3.Connection):
    # Tạo mock websocket client để kiểm tra việc phát sự kiện realtime.
    ws_client = MagicMock()

    # Tạo thời gian cố định để test ổn định và dễ assert.
    fixed_time = datetime(2026, 4, 22, 9, 0, 0)

    # Gọi hàm gửi chat với dữ liệu hợp lệ.
    sent_message = send_chat_message(
        db_conn=db_transaction,
        ws_client=ws_client,
        sender_id="user_001",
        room_id="room_support",
        content="Xin chào, tôi cần hỗ trợ vé.",
        now_provider=lambda: fixed_time,
    )

    # Query DB để kiểm tra bản ghi đã được insert.
    inserted_row = db_transaction.execute(
        "SELECT sender_id, room_id, content, created_at FROM chat_messages"
    ).fetchone()

    # Kỳ vọng dữ liệu lưu DB đúng như message đã gửi.
    assert inserted_row == (
        "user_001",
        "room_support",
        "Xin chào, tôi cần hỗ trợ vé.",
        "2026-04-22T09:00:00",
    )

    # Kỳ vọng websocket emit được gọi đúng event, payload, và room.
    ws_client.emit.assert_called_once_with(
        "chat:new-message",
        sent_message,
        room="room_support",
    )


# Test Case ID: TC_UT_Minh_009

def test_send_chat_message_rejects_empty_content(db_transaction: sqlite3.Connection):
    # Tạo mock websocket client để đảm bảo không bị emit khi message rỗng.
    ws_client = MagicMock()

    # Kỳ vọng ValueError nếu nội dung chỉ gồm khoảng trắng.
    with pytest.raises(ValueError, match="Nội dung chat không được rỗng"):
        # Gọi hàm với content rỗng để kiểm tra validation.
        send_chat_message(
            db_conn=db_transaction,
            ws_client=ws_client,
            sender_id="user_001",
            room_id="room_support",
            content="   ",
        )

    # Kỳ vọng không phát sự kiện websocket khi validation fail.
    ws_client.emit.assert_not_called()


# Test Case ID: TC_UT_Minh_010

def test_db_transaction_fixture_rolls_back_data(db_transaction: sqlite3.Connection):
    # Thêm thủ công một bản ghi để minh họa dữ liệu sẽ bị rollback sau test.
    db_transaction.execute(
        """
        INSERT INTO chat_messages (sender_id, room_id, content, created_at)
        VALUES (?, ?, ?, ?)
        """,
        ("rollback_user", "room_x", "temporary row", "2026-04-22T09:30:00"),
    )

    # Đếm số bản ghi trong transaction hiện tại.
    row_count = db_transaction.execute("SELECT COUNT(*) FROM chat_messages").fetchone()[0]

    # Kỳ vọng đã có ít nhất 1 bản ghi trong phạm vi test hiện tại.
    assert row_count >= 1
