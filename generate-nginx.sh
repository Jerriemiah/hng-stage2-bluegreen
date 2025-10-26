#!/bin/bash
# Only substitute known environment variables, not all $vars in file
envsubst '${ACTIVE_POOL}' < nginx.conf.template > nginx.conf
