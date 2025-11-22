@echo off
title Phan Mem Tra Cuu Hoa Chat
color 0A
echo ==================================================
echo      DANG KHOI DONG PHAN MEM TRA CUU HOA CHAT
echo ==================================================
echo.
echo Dang mo trinh duyet...
echo Nhan Ctrl+C trong cua so nay de tat phan mem.
echo.

:: Lệnh chạy Streamlit
streamlit run apptracuu.py

:: Giữ cửa sổ không bị tắt nếu có lỗi để kịp đọc
if %errorlevel% neq 0 (
    echo.
    echo CO LOI XAY RA! Vui long kiem tra lai code hoac thu vien.
    pause
)