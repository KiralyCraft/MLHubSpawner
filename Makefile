all:
	pip uninstall mlspawner -y
	python3 setup.py install
	echo "Restart jupyterhub!!"

