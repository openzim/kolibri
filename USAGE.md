# Usage of Kolibri2zim
Docker
------

- Clone the kolibri2zim repository to your local machine

- run the following command with the channel id and `name-of-the-zim` you are converting to .zim, `channel-id` is a 32-characters long ID that you can find in the URL of the channel you want, either from [Kolibri Studio](https://studio.learningequality.org) or the [Kolibri Catalog](https://kolibri-catalog-en.learningequality.org)

```bash
docker run -v my_dir:/output ghcr.io/openzim/kolibri kolibri2zim --channel-id `channel-id` --name `name-of-the-channel`
```

- This will create a `.zim` file in the `/output` file, which will be persisted in the my_dir Docker volume.

-For getting this .zim file on to your local machine you can save it to your desktop by using `save` command.

- For opening this `.zim` file, you need a ZIM reader, you could use a Kiwix one and you might use [kiwix-serve](https://kiwix.org/en/applications/).

- now you can access that created `.zim` file from the `kiwix-serve ui` and start the server on the localhost.

- Whenever you make code changes during development, you need to create a Docker image of your modified code using

```bash
docker build -t `your-image-name`:`version` .
```
- Here, "your-image-name" would be replaced with the name you choose for your Docker image, and "version" would be replaced with a version tag, like "latest," "v1.0," etc. this image is for local use only, and thus doesn't need to follow any standardized naming or versioning conventions.

- You need to run that image going into the `images` section in docker.

```bash
docker run -v my_dir:/output `your-image-name:version` kolibri2zim --channel-id `channel-id` --name `name-of-the-zim`
```
