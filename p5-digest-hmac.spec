### RPM external p5-digest-hmac 1.02
## INITENV +PATH PERL5LIB %i/lib/site_perl/%perlversion
%define perl /usr/bin/env perl
%if "%(echo %cmsplatf | cut -f1 -d_ | sed -e 's|\([A-Za-z]*\)[0-9]*|\1|')" == "osx"
%define perl /usr/bin/perl
%endif

%define perlversion %(%perl -e 'printf "%%vd", $^V')
%define downloadn Digest-HMAC
Source: http://search.cpan.org/CPAN/authors/id/G/GA/GAAS/%{downloadn}-%{realversion}.tar.gz
Requires: p5-digest-sha1

%prep
%setup -n %downloadn-%realversion

%build
LC_ALL=C; export LC_ALL
%perl Makefile.PL PREFIX=%i LIB=%i/lib/site_perl/%perlversion
make
make install

%install
