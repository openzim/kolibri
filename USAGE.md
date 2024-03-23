# Usage of Kolibri2zim using Docker

- Clone the kolibri2zim repository from here to your local machine

- cd into its new_ui branch

- run the following command with the channel id and name of the channel you are converting to to .zim

```bash
docker run -v my_dir:/output ghcr.io/openzim/kolibri kolibri2zim --channel-id `channel-id` --name `name-of-the-channel`
```

- This will create a `.zim` file in the `/output` file in the docker container.

-For getting this .zim file on to your local machine you can save it to your desktop by using `save` option from docker.

- For rendering this `.zim` file, you need to setup [kiwix-server](https://kiwix.org/en/applications/).

- now you can access that created `.zim` file from the `kiwix-server ui` and start the server on the localhost.

- Whenever you make changes in the code during devepment, you need to create a docker image of your modified code using

```bash
docker build -t `your-image-name`:`version` .
```

- You need to run that image going into the `images` section in docker.

- Then run this command to create the `.zim` file using your modified code, run-

```bash
docker run -v my_dir:/output `your-image-name` kolibri2zim --channel-id `channel-id` --name `name-of-the-channel`
```
