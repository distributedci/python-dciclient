#!/bin/sh

usage()
{
  echo "Usage: $0 <TOPIC> <DOWNLOAD_LOCATION>"
  echo ""
  echo "Examples:"
  echo "      $0 RHEL-9.0 /opt/beaker/dci"
  echo "      $0 RHEL-8.7 /opt/beaker/dci"
  exit 2
}

TOPIC=$1
BASEDIR=$2
if [ -z "$TOPIC" -o -z "$BASEDIR" ]; then
   usage
fi

if [ -e "/etc/dci-rhel-agent/dcirc.sh" ]; then
   . /etc/dci-rhel-agent/dcirc.sh
fi

KERNEL=$(dci-rhel-latest-kernel-version --topic $TOPIC)

if [ $? -ne 0 ]; then
   echo "No z-stream kernel"
   exit 2
fi

if [ -e "$BASEDIR/$TOPIC/compose/metadata/rpms.json" ]; then
   PREV_KERNEL=$(jq -r '.payload.rpms.BaseOS.x86_64 | keys | map(capture("kernel-.*:(?<ver>.*).src"))[].ver' $BASEDIR/$TOPIC/compose/metadata/rpms.json)
else
   PREV_KERNEL=""
fi

if [ "$KERNEL" != "$PREV_KERNEL" ]; then
   echo $KERNEL
   exit 0
else
   exit 1
fi

