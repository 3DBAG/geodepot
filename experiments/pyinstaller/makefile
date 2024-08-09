conda-create:
	conda create -n geodepot-experiment-pyinstaller-py312 -c conda-forge python=3.12 proj pyproj click pyinstaller
	conda install -n geodepot-experiment-pyinstaller-py312 -c conda-forge gdal pdal python-pdal

conda-remove:
	conda env remove -n geodepot-experiment-pyinstaller-py312

compile:
	pyinstaller --name geodepot --onedir --noconfirm --optimize 2 --collect-all pdal --collect-all osgeo cli.py

# Requires: nuitka, libpython-static (on conda), patchelf, ordered-set
compile-nuitka:
	python -m nuitka --standalone --jobs=6 --follow-import-to=osgeo --follow-import-to=pdal cli.py