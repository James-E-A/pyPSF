import setuptools

setuptools.setup(
	name="pypsf",
	version="0.2.0",
	author="James Edington",
	author_email="james@ishygddt.xyz",
	description="Library for interacting with PC Screen Font files",
	packages=setuptools.find_packages(),
	classifiers=[
	 "Development Status :: 4 - Beta",
	],
	include_package_data=True,
	install_requires=["Pillow"]
)
