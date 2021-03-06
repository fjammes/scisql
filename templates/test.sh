#!/usr/bin/env sh

DIR=$(cd "$(dirname "$0")"; pwd -P)                                                                     

SCISQL_BASE={{SCISQL_BASE}}
export SCISQL_PREFIX={{SCISQL_PREFIX}}
export MYSQL_CNF=${DIR}/my-client.cnf
export MYSQL={{MYSQL_BIN}}

retcode=0
for testfile in ${SCISQL_BASE}/test/test*.py ${SCISQL_BASE}/tools/docs.py
do
    echo -n "Running ${testfile} : "
    if python ${testfile}; then
        echo "PASS"
    else
        echo "FAIL"
        retcode=1
    fi
done

if [ ${retcode} -eq 0 ]; then
    echo "sciSQL deployment tests SUCCESSFUL"
else
    >&2 echo "sciSQL deployment tests FAILED"
    exit 1
fi
exit ${retcode}
