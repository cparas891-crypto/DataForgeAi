from PyInstaller.utils.hooks import collect_all


datas = [
    ("templates", "templates"),
]

binaries = []

hiddenimports = []


packages = [
    "fastapi",
    "starlette",
    "jinja2",
    "uvicorn",
    "pandas",
    "plotly",
    "reportlab",
    "openpyxl",
    "multipart",
]


for package in packages:

    try:

        package_datas, package_binaries, package_hiddenimports = (
            collect_all(
                package
            )
        )

        datas += package_datas

        binaries += package_binaries

        hiddenimports += package_hiddenimports

    except Exception:

        pass


a = Analysis(
    ["launcher.py"],

    pathex=[],

    binaries=binaries,

    datas=datas,

    hiddenimports=hiddenimports,

    hookspath=[],

    hooksconfig={},

    runtime_hooks=[],

    excludes=[],

    noarchive=False,
)


pyz = PYZ(
    a.pure
)


exe = EXE(
    pyz,

    a.scripts,

    [],

    exclude_binaries=True,

    name="DataForgeAI",

    debug=False,

    bootloader_ignore_signals=False,

    strip=False,

    upx=True,

    console=True,

    disable_windowed_traceback=False,
)


coll = COLLECT(
    exe,

    a.binaries,

    a.datas,

    strip=False,

    upx=True,

    upx_exclude=[],

    name="DataForgeAI",
)