FROM tsaiid/cx_oracle:16.04
MAINTAINER I-Ta Tsai <itsai@gmail.com>

# Application layer
# -- Install Application into container:
RUN set -ex && mkdir /app
WORKDIR /app

# python packages
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt gunicorn

COPY . ./webapp

CMD ["gunicorn", "-b:8000", "webapp:app"]
