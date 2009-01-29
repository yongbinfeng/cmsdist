### RPM cms dqmgui 4.3.0j

%define cvsserver   cvs://:pserver:anonymous@cmscvs.cern.ch:2401/cvs_server/repositories/CMSSW?passwd=AA_:yZZ3e
%define scram       $SCRAMV1_ROOT/bin/scram --arch %cmsplatf
%define cmssw       CMSSW_2_2_3
%define vcfg        V03-17-02
%define initenv     export ZZPATH=$PATH ZZLD_LIBRARY_PATH=$LD_LIBRARY_PATH ZZPYTHONPATH=$PYTHONPATH; %initenv_all

Source0: %{cvsserver}&strategy=checkout&module=config&export=config&tag=-r%{vcfg}&output=/config.tar.gz
Source1: %{cvsserver}&strategy=checkout&module=CMSSW/VisMonitoring/DQMServer&export=VisMonitoring/DQMServer&tag=-rV04-03-00&output=/DQMServer.tar.gz
Source2: %{cvsserver}&strategy=checkout&module=CMSSW/DQM/RenderPlugins&export=DQM/RenderPlugins&tag=-rV04-02-00&output=/DQMRenderPlugins.tar.gz
Source3: %{cvsserver}&strategy=checkout&module=CMSSW/Iguana/Utilities&export=Iguana/Utilities&tag=-r%{cmssw}&output=/IgUtils.tar.gz
Source4: %{cvsserver}&strategy=checkout&module=CMSSW/Iguana/Framework&export=Iguana/Framework&tag=-r%{cmssw}&output=/IgFramework.tar.gz
Source5: %{cvsserver}&strategy=checkout&module=CMSSW/DQMServices/Core&export=DQMServices/Core&tag=-r%{cmssw}&output=/DQMCore.tar.gz
Source6: %{cvsserver}&strategy=checkout&module=CMSSW/FWCore&export=FWCore&tag=-r%{cmssw}&output=/FWCore.tar.gz
Source7: %{cvsserver}&strategy=checkout&module=CMSSW/DataFormats&export=DataFormats&tag=-r%{cmssw}&output=/DataFormats.tar.gz
Requires: cherrypy py2-cheetah yui py2-pysqlite py2-cx-oracle py2-pil py2-matplotlib dqmgui-conf SCRAMV1

%prep
rm -fr %_builddir/{config,src,THE_BUILD}
%setup    -T -b 0 -n config
%setup -c -T -a 1 -n src
%setup -D -T -a 2 -n src
%setup -D -T -a 3 -n src
%setup -D -T -a 4 -n src
%setup -D -T -a 5 -n src
%setup -D -T -a 6 -n src
%setup -D -T -a 7 -n src

cd %_builddir
rm -fr src/FWCore/Framework/bin
rm -fr src/{FWCore,DataFormats,DQM*}/*/test
for f in src/FWCore/* src/DataFormats/*; do
  case $f in
    */FWCore/Framework | \
    */FWCore/MessageLogger | \
    */FWCore/MessageService | \
    */FWCore/ParameterSet | \
    */FWCore/PluginManager | \
    */FWCore/ServiceRegistry | \
    */FWCore/Utilities | \
    */FWCore/Version | \
    */DataFormats/Common | \
    */DataFormats/Provenance | \
    */DataFormats/*StdDictionaries )
      ;;
    * )
      rm -fr $f ;;
  esac
done

config/updateConfig.pl -p CMSSW -v THE_BUILD -s $SCRAMV1_VERSION -t ${DQMGUI_CONF_ROOT}
%scram project -d $PWD -b config/bootsrc.xml

%build
# Build the code as a scram project area, then relocate it to more
# normal directories (%i/{bin,lib,python}).  Save the scram runtime
# environment plus extra externals for later use, but manipulate
# the scram environment to point to the installation directories.
# Avoid generating excess environment.
cd %_builddir/THE_BUILD/src
export BUILD_LOG=yes
export SCRAM_NOPLUGINREFRESH=yes
export SCRAM_NOLOADCHECK=true
export SCRAM_NOSYMCHECK=true
(unset GCCXML_ROOT && %scram build -v -f %makeprocesses </dev/null) || { %scram build outputlog && false; }
rm -f ../lib/*/.*cache
(eval `%scram run -sh` ; SealPluginRefresh) || true
(eval `%scram run -sh` ; EdmPluginRefresh) || true
(eval `%scram run -sh` ; IgPluginRefresh) || true

mkdir -p %i/etc/profile.d
for p in PATH LD_LIBRARY_PATH PYTHONPATH; do
  for z in "" ZZ; do
    eval export $z$p=$(perl -e 'print join(":", grep($_ && -d $_ && scalar(@{[<$_/*>]}) > 0, split(/:/,$ENV{'$z$p'})))')
  done
done
scram runtime -sh | grep -v SCRAMRT > %i/etc/profile.d/env.sh
scram runtime -csh | grep -v SCRAMRT > %i/etc/profile.d/env.csh
perl -w -i -p -e \
  'BEGIN {
     %%linked = map { s|/+[^/]+$||; ($_ => 1) }
                grep(defined $_, map { readlink $_ }
                     <%_builddir/THE_BUILD/external/%cmsplatf/lib/*>);
   }
   foreach $dir (keys %%linked) { s<:$dir([ :;"]|$)><$1>g; }
   foreach $p ("PATH", "LD_LIBRARY_PATH", "PYTHONPATH") {
     s<([ :=])$ENV{"ZZ$p"}([ :;"]|$)><$1\${$p}$2>g if $ENV{"ZZ$p"};
   }
   s<%_builddir/THE_BUILD/bin/%cmsplatf><%i/bin>g;
   s<%_builddir/THE_BUILD/(lib|module)/%cmsplatf><%i/lib>g;
   s<%_builddir/THE_BUILD/external/%cmsplatf/lib><%i/external>g;
   s<%_builddir/THE_BUILD/python><%i/python>g;
   s<%_builddir/THE_BUILD><%i>g;' \
  %i/etc/profile.d/env.sh %i/etc/profile.d/env.csh

(echo "export PATH=%i/xbin:\$PATH;"
 echo "export PYTHONPATH=%i/xlib:%i/xpython:\$PYTHONPATH;"
 echo "export LD_LIBRARY_PATH=%i/xlib:\$LD_LIBRARY_PATH;"
 echo "export YUI_ROOT='$YUI_ROOT';"
 echo "export DQM_CMSSW_VERSION='%{cmssw}';") >> %i/etc/profile.d/env.sh

(echo "setenv PATH %i/xbin:\$PATH;"
 echo "setenv PYTHONPATH %i/xlib:%i/xpython:\$PYTHONPATH;"
 echo "setenv LD_LIBRARY_PATH %i/xlib:\$LD_LIBRARY_PATH;"
 echo "setenv YUI_ROOT '$YUI_ROOT';"
 echo "setenv DQM_CMSSW_VERSION '%{cmssw}';") >> %i/etc/profile.d/env.csh

%install
mkdir -p %i/etc %i/external %i/{,x}bin %i/{,x}lib %i/{,x}python
cp -p %_builddir/THE_BUILD/lib/%cmsplatf/.{iglets,edmplugincache} %i/lib
cp -p %_builddir/THE_BUILD/lib/%cmsplatf/*.{so,edm,ig}* %i/lib
cp -p %_builddir/THE_BUILD/bin/%cmsplatf/{vis*,Ig*,edm*,DQMCollector} %i/bin
cp -p %_builddir/THE_BUILD/src/VisMonitoring/DQMServer/python/*.* %i/python
tar -C %_builddir/THE_BUILD/external/%cmsplatf/lib -cf - . | tar -C %i/external -xvvf -

(echo '#!/bin/sh';
 echo 'doit= shopt=-ex'
 echo 'while [ $# -gt 0 ]; do'
 echo ' case $1 in'
 echo '  -n ) doit=echo shopt=-e; shift ;;'
 echo '  * )  echo "$0: unrecognised parameter: $1" 1>&2; exit 1 ;;'
 echo ' esac'
 echo 'done'
 echo 'set $shopt'
 cd %_builddir/THE_BUILD/src
 for f in */*/CVS/Tag; do
   [ -f $f ] || continue
   tag=$(cat $f | sed 's/^N//')
   pkg=$(echo $f | sed 's|/CVS/Tag||')
   echo "\$doit cvs -Q co -r $tag $pkg"
 done) > %i/bin/visDQMDistSource

sed 's/^  //' > %i/bin/visDQMDistPatch << \END_OF_SCRIPT
  #!/bin/sh

  if [ X"$CMSSW_BASE" = X%i ]; then
    unset CMSSW_BASE
  fi

  if [ X"$CMSSW_BASE" = X ]; then
    echo "warning: local scram runtime environment not set, sourcing now" 1>&2
    eval `scram runtime -sh`
  fi

  if [ X"$CMSSW_BASE" = X ] || [ X"$SCRAM_ARCH" = X ] || \
     [ ! -f "$CMSSW_BASE/lib/$SCRAM_ARCH/.iglets" ]; then
    echo "error: could not locate local scram developer area, exiting" 1>&2
    exit 1;
  fi

  set -e
  rm -fr %i/x{lib,bin,python}/{*,.??*}

  echo "copying $CMSSW_BASE/lib/$SCRAM_ARCH into %i/xlib"
  (cd $CMSSW_BASE/lib/$SCRAM_ARCH && tar -cf - .) | (cd %i/xlib && tar -xvvf -)

  echo "copying $CMSSW_BASE/bin/$SCRAM_ARCH into %i/xbin"
  (cd $CMSSW_BASE/bin/$SCRAM_ARCH && tar -cf - .) | (cd %i/xbin && tar -xvvf -)

  echo "copying $CMSSW_BASE/src/VisMonitoring/DQMServer/python into %i/xpython"
  (cd $CMSSW_BASE/src/VisMonitoring/DQMServer/python && tar -cf - *.*) | (cd %i/xpython && tar -xvvf -)
  exit 0
END_OF_SCRIPT

sed 's/^  //' > %i/bin/visDQMDistUnpatch << \END_OF_SCRIPT
  #!/bin/sh
  echo "removing local overrides from %i"
  rm -fr %i/x{lib,bin,python}/{*,.??*}
  exit 0
END_OF_SCRIPT

sed 's/^  //' > %i/etc/restart-collector << \END_OF_SCRIPT
  #!/bin/sh
  . %instroot/cmsset_default.sh
  . %i/etc/profile.d/env.sh
  killall -9 DQMCollector
  set -e
  for opt; do
    case $opt in
      :* )  port= dir=$(echo $opt | sed 's/.*://') ;;
      *:* ) dir=$(echo $opt | sed 's/.*://')
            port=$(echo $opt | sed 's/:.*//') ;;
      * )  port= dir=$opt ;;
    esac

    mkdir -p $dir/collector
    cd $dir/collector
    [ ! -f collector.out ] || mv -f collector.out collector.out.$(date +%%Y%%m%%d%%H%%M%%S)
    DQMCollector ${port:+ --listen $port} > collector.out 2>&1 </dev/null &
  done
END_OF_SCRIPT

sed 's/^  //' > %i/etc/archive-collector-logs << \END_OF_SCRIPT
  #!/bin/sh
  for opt; do
    dir=$(echo $opt | sed 's/.*://')
    cd $dir/collector
    for month in $(ls | fgrep collector.out. | sed 's/.*out.\(......\).*/\1/' | sort | uniq); do
      zip -rm collector-$month.zip collector.out.$month*
    done
  done
END_OF_SCRIPT

sed 's/^  //' > %i/etc/purge-old-sessions << \END_OF_SCRIPT
  #!/bin/sh
  . %instroot/cmsset_default.sh
  . %i/etc/profile.d/env.sh
  for opt; do
    [ -d "$opt/gui/www/sessions" ] || continue
    visDQMPurgeSessions $opt/gui/www/sessions
  done
END_OF_SCRIPT

sed 's/^  //' > %i/etc/update-crontab << \END_OF_SCRIPT
  #!/bin/sh
  collector= defcollector=9090:$(dirname %instroot)
  purge= defpurge=$(dirname %instroot)
  while [ $# -gt 0 ]; do
    case $1 in
      --collector )
        collector="$collector $2"
        shift; shift ;;
      --purge )
        purge="$purge $2"
        shift; shift ;;
      * )
        echo "$(basename $0): unrecognised option $1" 1>&2
        exit 1 ;;
    esac
  done

  set -x
  (crontab -l | fgrep -v /dqmgui/;
   sed -e "s|#COLLECTOR|${collector:-$defcollector}|g" \
       -e "s|#PURGE|${purge:-$defpurge}|g" <%i/etc/crontab) |
  crontab -
END_OF_SCRIPT

sed 's/^  //' > %i/etc/crontab << \END_OF_SCRIPT
  5 */2 * * * %i/etc/purge-old-sessions #PURGE
  0 0 * * * %i/etc/restart-collector #COLLECTOR
  20 0 1 * * %i/etc/archive-collector-logs #COLLECTOR
END_OF_SCRIPT

chmod a+x %i/bin/visDQMDist*
chmod a+x %i/etc/*-*

%post
%{relocateConfig}bin/visDQMDist*
%{relocateConfig}etc/*-*
%{relocateConfig}etc/crontab
%{relocateConfig}etc/profile.d/env.sh
%{relocateConfig}etc/profile.d/env.csh
perl -w -e '
  ($oldroot, $newroot, @files) = @ARGV;
  foreach $f (@files) {
    next if !defined($old = readlink $f);
    ($new = $old) =~ s|\Q$oldroot\E|$newroot|;
    if ($new ne $old) { unlink($f); symlink($new, $f); }
  }' %instroot $RPM_INSTALL_PREFIX $RPM_INSTALL_PREFIX/%pkgrel/external/*
