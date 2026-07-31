import os
from glob import glob
from setuptools import setup

package_name = 'robot_security'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'policies'), glob('policies/*.xml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Tarun R',
    maintainer_email='tarun.ramak@gmail.com',
    description='Automated SROS2 keystore and policy generation for Smart Wheelchair',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'generate_keystore = robot_security.generate_keystore:main'
        ],
    },
)
