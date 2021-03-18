#!/bin/bash
# Copyright 2020 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

USER_ID=`id -u`
GROUP_ID=`id -g`

echo "Attempting to make changes to the docker config to have credentials work."

CONTAINER_EXIST=`sudo docker container list 2>&1 | grep -w notebook`
if [ "x${CONTAINER_EXIST}" == "x" ]
then
  echo "Notebook container is not up and running, run it first."
  exit 1
fi

# Create a symbolic link to the user's home directory (for token access).
HOME_PATH=`dirname "${HOME}"`
HOME_DIR=`basename "${HOME}"`

sudo docker exec -u root notebook mkdir -p "${HOME_PATH}"
sudo docker exec -u root notebook ln -s "/home/picatrix" "${HOME}" 

echo " - [DONE] Symbolic link to created for token paths."

if [ ${USER_ID} -eq 1000 ]
then
  echo " - [DONE] No need to make any changes, user has the same UID."
else
  # Change UID/GID of the user to match user on the machine.
  sudo docker exec -u root notebook usermod -u "${USER_ID}" picatrix
  sudo docker exec -u root notebook usermod -g "${GROUP_ID}" picatrix
  sudo docker exec -u root notebook chown -R picatrix:picatrix /home/picatrix

  echo " - [DONE] UID for the container user has been changed to '${USER_ID}'"
fi

echo ""
echo "Please re-start the docker container to make sure things are working again."
