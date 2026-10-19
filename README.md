# TaskHub API

Project thực hành FastAPI đến hết mục 3 của lộ trình: setup, CRUD nền tảng, quan hệ SQLAlchemy và truy vấn lồng nhau. Mặc định dùng SQLite; PostgreSQL và MySQL có thể bật qua extra driver và `DATABASE_URL`.

## Chạy trên Windows

Yêu cầu Python 3.12 hoặc 3.13 (các lệnh bên dưới dùng Python 3.12).

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Mở [Swagger UI](http://127.0.0.1:8000/docs). Database SQLite `taskhub.db` được tạo trong thư mục hiện hành khi chạy migration.

Lưu ý: `requirements.lock` hiện có cả driver PostgreSQL (`psycopg`) và MySQL (`PyMySQL`), nên các lệnh cài đặt ở trên sẽ cài cả hai dù SQLite vẫn là database mặc định. Để cài chỉ các dependency cơ bản cho SQLite, thay hai lệnh cài package ở trên bằng:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

Để chỉ cài driver PostgreSQL hoặc MySQL từ `pyproject.toml`, dùng `python -m pip install -e ".[postgres]"` hoặc `python -m pip install -e ".[mysql]"` thay cho các lệnh cài package ở trên.

## Database

Ứng dụng đọc `DATABASE_URL` từ biến môi trường hoặc `.env`. Ví dụ PostgreSQL:

```dotenv
DATABASE_URL=postgresql+psycopg://taskhub:password@localhost:5432/taskhub
```

Ví dụ MySQL:

```dotenv
DATABASE_URL=mysql+pymysql://taskhub:password@localhost:3306/taskhub
```

Không đưa thông tin xác thực thật vào `.env.example` hoặc Git. Mỗi thay đổi schema cần tạo migration bằng `alembic revision --autogenerate -m "mo-ta-thay-doi"`, xem lại migration rồi chạy `alembic upgrade head`.

## API trong phạm vi mục 1–3

- `POST /api/users` tạo user; `GET /api/users/{username}/profile` trả profile cùng danh sách project.
- `GET /api/projects`, `POST /api/projects`, `GET /api/projects/{project_id}`, `PATCH /api/projects/{project_id}`, `DELETE /api/projects/{project_id}`.
- `GET /api/projects/{project_id}/tasks`, `POST /api/projects/{project_id}/tasks`.
- `GET /api/tags`, `POST /api/tags`.

Tạo user trước, rồi tạo project với `owner_id`; tạo tag trước nếu muốn gắn `tag_ids` vào task. Chi tiết request/response được hiển thị tại `/docs`.

Phạm vi API hiện tại không có endpoint cho comment hoặc authentication.

## Cấu trúc

- `app/models/`: SQLAlchemy models và bảng nối Task–Tag.
- `app/schemas/`: Pydantic request/response models.
- `app/crud/`: thao tác dữ liệu và truy vấn eager loading.
- `app/api/routes/`: FastAPI routers.
- `app/db/` và `migrations/`: engine, session dependency, Alembic.
- `docs/`: roadmap, kiến trúc, quy ước và changelog.
