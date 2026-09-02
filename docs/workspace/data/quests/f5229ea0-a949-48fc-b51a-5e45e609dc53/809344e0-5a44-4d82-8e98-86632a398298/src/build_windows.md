./autogen.sh
________________________________________________
export CC=x86_64-w64-mingw32-gcc
export CXX=x86_64-w64-mingw32-g++
export CXXFLAGS="-std=gnu++14 -O2 -pipe"
export CPPFLAGS="-I/c/db4/include -I/c/boost/1.74.0/include"
export LDFLAGS="-L/c/db4/lib -L/c/boost/1.74.0/lib -L/c/openssl/3.3.1/lib -L/c/libevent/2.1.12/lib -L/c/zeromq/4.3.5/lib"
export PKG_CONFIG_PATH="/c/openssl/3.3.1/lib/pkgconfig:/c/libevent/2.1.12/lib/pkgconfig:/c/zeromq/4.3.5/lib/pkgconfig"
export PKG_CONFIG='pkgconf --static'

./configure \
  --build=x86_64-w64-mingw32 \
  --host=x86_64-w64-mingw32 \
  --without-gui \
  --disable-bench \
  --with-zmq \
  --with-miniupnpc=no \
  --with-boost=/c/boost/1.74.0 \
  --with-boost-libdir=/c/boost/1.74.0/lib

make -j"$(nproc)" \
  LDFLAGS="$LDFLAGS -static -static-libstdc++ -static-libgcc" \
  LIBS="-ldb_cxx-4.8 \
        -lboost_system-mt -lboost_filesystem-mt -lboost_thread-mt -lboost_chrono-mt -lboost_program_options-mt \
        -lzmq -levent -levent_openssl -lssl -lcrypto \
        -lws2_32 -liphlpapi -lcrypt32 -lbcrypt -lrpcrt4 -luser32 -lntdll -lwinpthread"
