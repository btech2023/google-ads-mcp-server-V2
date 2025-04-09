from setuptools import setup, find_packages

setup(
    name="google_ads_mcp_server",
    version="0.1.0",
    packages=find_packages(include=['google_ads_mcp_server', 'google_ads_mcp_server.* ']),
    # Add other dependencies here if needed for the package itself
    # install_requires=[], 
    # Tests require additional packages, but they aren't needed for the package itself
    extras_require={
        'test': ['pytest', 'unittest.mock'],
    },
    entry_points={
        'console_scripts': [
            'google-ads-mcp-server=google_ads_mcp_server.main:main',
        ],
    },
) 