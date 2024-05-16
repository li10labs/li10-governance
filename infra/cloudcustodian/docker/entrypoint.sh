#!/bin/bash

cd /governance

aws sts get-caller-identity 

source .venv/bin/activate

mkdir .cache

for dir in /governance/policy/*/
do
    echo "working with policies in directory: $dir"
    echo "test policy: $POLICY_FILTER"

    for policy_file in $dir*.yml
    do
        echo "processing $policy_file"

        if [[ $policy_file != *accounts.yml ]]
        then
            if [ "$dir$POLICY_FILTER" = $policy_file ]; then
                echo "execute (1).$policy_file."
                c7n-org run  --cache-period 0 --cache-path ./.cache/ -c $dir/accounts.yml -s out -u $policy_file --verbose --debug
            elif [ -z "$POLICY_FILTER" ]; then
                echo "execute (2) .$policy_file."
                c7n-org run  --cache-period 0 --cache-path ./.cache/ -c $dir/accounts.yml -s out -u $policy_file --verbose --debug
            else
                echo "skip .$policy_file."
            fi
        else
            echo "skipping $policy_file"
        fi
    done
done

ls -als /governance/out 
echo "Done processing all policies"