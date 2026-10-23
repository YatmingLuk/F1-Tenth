import os
from glob import glob

from setuptools import find_packages, setup


package_name = 'vehicle_state_estimator'

setup(
    name=package_name,
    version='0.2.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Yiming Lu',
    maintainer_email='thswx5201314yiming@gmail.com',
    description='Estimate planar vehicle motion from Cartographer TF poses.',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'cartographer_velocity = '
            'vehicle_state_estimator.cartographer_velocity:main',
        ],
    },
)
