"""MES Platform — backend.

    modules/   11 lát cắt dọc, mỗi thư mục một tính năng
    common/    hạ tầng mọi module đều dùng
    db/        engine, session, migrations
    router.py  gộp router của 10 module có endpoint, prefix /v1
    main.py    tạo FastAPI, middleware, healthz, ánh xạ lỗi

Cắt DỌC theo tính năng, không cắt ngang theo tầng: mở một thư mục trong `modules/`
là thấy đủ models · schemas · repository · service · router của tính năng đó.
"""
