import os
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Get the URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# FORCE the dialect to aiomysql if it's currently mysql://
if DATABASE_URL and DATABASE_URL.startswith("mysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+aiomysql://")

# Intercept SSL configuration to prevent asyncio/aiomysql crashes
connect_args = {}
if DATABASE_URL and ("ssl=" in DATABASE_URL or "ssl_ca" in DATABASE_URL or "ssl-mode" in DATABASE_URL or "aivencloud.com" in DATABASE_URL):
    # Strip problematic query parameters from the URL string
    for param in ["?ssl=true", "&ssl=true", "?ssl_ca=/etc/ssl/certs/ca-certificates.crt", "&ssl_ca=/etc/ssl/certs/ca-certificates.crt", "?ssl-mode=REQUIRED", "&ssl-mode=REQUIRED"]:
        DATABASE_URL = DATABASE_URL.replace(param, "")
        
    # Create a secure SSLContext
    ssl_context = ssl.create_default_context()
    
    # Custom Aiven CA Certificate
    aiven_ca_cert = """-----BEGIN CERTIFICATE-----
MIIERDCCAqygAwIBAgIUUdbLI703HROTkpm/v71tI2C91OEwDQYJKoZIhvcNAQEM
BQAwOjE4MDYGA1UEAwwvMTBjNWFmOWYtMWZiYi00MGFlLWEwYzAtMzVjMGI1OWYw
OWUzIFByb2plY3QgQ0EwHhcNMjYwNjEyMDgzMzM5WhcNMzYwNjA5MDgzMzM5WjA6
MTgwNgYDVQQDDC8xMGM1YWY5Zi0xZmJiLTQwYWUtYTBjMC0zNWMwYjU5ZjA5ZTMg
UHJvamVjdCBDQTCCAaIwDQYJKoZIhvcNAQEBBQADggGPADCCAYoCggGBAKzhphZh
QKwFFnOPlN+6HftxPBiUNao87OKJNghSwjyPP3Djp0rpNJMPBG/b6o6wa9DGUZXO
4S9zzWw0DI/WYT4TWpBBYr7xqzyckxcaxPMcEXQW7a3pCpXIMyX/jbQJNtyMV6E4
enzN2/WHtcdRYQmwnMZcYfUFwqlv3af9DVHzmDjS2g2OwU0sOPux/GrCPukp+wWv
Lha5TupBVNDh40p3eeihXv53zwVYOoK03ZYfRkodlrnn2yewn3kfp3Fv9fpOPkKn
Naq6iiqn2e/pUOiDrSYkVWZUWOfP2NxwMzZhPyJ86ZJ2CwcmfndoGAHOrVpGiMRg
FF7Vt29FsetjKIBUpnPeJYMs9nPNdV7q3+avoH7vKn4eU/UXCA+btpp/WjkfMchr
3YFvIwpuaZcakIG1NaT3Drc6vb60vc6+SpBISHwBOprrgGmIbByzXptIvN/J1WSX
68RUGsVAFyTGaXTka5FWIJh9YH1JC2e4C7ONmjVZdK+50KibsyV7AGupYQIDAQAB
o0IwQDAdBgNVHQ4EFgQUaQrbnbAVEQFKkcsJmQ6DOWp4/jwwEgYDVR0TAQH/BAgw
BgEB/wIBADALBgNVHQ8EBAMCAQYwDQYJKoZIhvcNAQEMBQADggGBAAp0XWqawmRC
Oo2Y8GzX91sVSyzvgMmrxyURyIZbq33sczlan9wqD6AR7e9SrUpDZgxrt9OuA44j
8UgxVg4T/Hf7Z5m7LiL+Mx0XTVMJjIqt+zp7q8d5WuSLAXefgzv5ALGZFRjfKalz
HrcKLyKn5jwXIPHhnKyB0YUx+fetx8UZCPsUurNUnet9QqbFoeYG5XohVi0I5c27
OFq1Zo2yIYqFCPYhzgdhXp1llQQh4Fr1t3V7Dyq+DDgx+n2I/lA8DMN7Jq8BsB9L
CNpxPcVjgwTVT+dSJj99gz16yWVRaSbxBTsD+56afQOuHOtXs07ULWsD7FHcTG+x
WeG107c9QRjrjIFsj40u21gZcvyyHZ6Uj44DLCgwcMf/Bgep7FUafh5Dz/rFqh0A
vDF69fiHqJEf6TmofAZ761Gg3zaQfmdz1TaF6tcAUqO9E7iX4+zRuZ3f0Xxcx42t
kmdTna2bqdoCOek0eidn6wCvSLjQ9Q2tS1mFHOxLNqtBEF35T+m10Q==
-----END CERTIFICATE-----"""

    # Load custom CA certificate from the PEM string directly in memory
    ssl_context.load_verify_locations(cadata=aiven_ca_cert)
    connect_args["ssl"] = ssl_context

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    connect_args=connect_args
)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session