from setuptools import setup

setup(
    name='py-msm',
    version='0.4.2',
    packages=['py_msm'],
    install_requires=['GitPython', 'typing'],
    url='https://github.com/MycroftAI/mycroft-skills-manager',
    license='MIT',
    author='jarbasAI, Matthew Scholefield',
    author_email='jarbasai@mailfence.com, matthew331199@gmail.com',
    description='Mycroft Skills Manager',
    entry_points={
        'console_scripts': {
            'msm=py_msm.__main__:main'
        }
    }
)
