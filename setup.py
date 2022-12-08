from setuptools import setup, find_packages


packages = find_packages('src', include=('mamba_to_pytest*',))


setup(
    name='mamba_to_pytest',
    version='0.0.1',
    license='MIT',
    description=f'mamba_to_pytest',
    author='tim@diels.me',
    package_dir={'': 'src'},
    packages=packages,
    entry_points={
        'console_scripts': ['mamba_to_pytest=mamba_to_pytest.main:main'],
    },
)
