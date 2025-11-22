@echo off
title Cai Dat Thu Vien
color 0B
echo ==================================================
echo      DANG CAI DAT TAVILY (TIM KIEM CHUYEN SAU)...
echo ==================================================

:: Cài tavily-python
pip install streamlit pubchempy requests stmol py3Dmol ipython_genutils rdkit chempy mendeleev tavily-python

echo.
echo DA CAI DAT XONG!
pause