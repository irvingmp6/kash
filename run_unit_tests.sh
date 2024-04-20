set -x
python -m coverage run -m unittest discover
coverage report > unittest_coverage_report.txt
coverage html -d unittest_coverage_report
cat unittest_coverage_report.txt
start "unittest_coverage_report/index.html"
