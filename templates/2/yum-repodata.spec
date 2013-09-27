%define distname {{ repo.reponame }}-{{ repo.version }}
{% if keyid is defined and keyid != false %}%define gpgkey RPM-GPG-KEY-{{ repo.reponame }}-{{ repo.version }}{% endif %}

Name:           {{ repo.reponame }}-release
Version:        {{ repo.version }}
Release:        1%{?dist}
Summary:        Yum .repo files for {{ repo.reponame }}
Group:          System Environment/Base
License:        MIT
URL:            {{ repo.url }}/
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
Requires:       yum
# NOTE: .repo file does not depends on arch but mock.cfg does.
Source0:        {{ repo.reponame }}.repo
{% for arch in repo.archs -%}
Source{{ loop.index }}:        %{distname}-{{ arch }}.cfg
{% endfor -%}
{% if keyid is defined and keyid != false %}Source100:      %{gpgkey}{% endif %}

%description
Yum repo and related config files of {{ repo.reponame }}.

This package contains yum repo (.repo) file.


%package -n     %{distname}-mockbuild-data
Summary:        Mockbuild config files for %{distname}
Group:          Development/Tools
Requires:       mock


%description -n %{distname}-mockbuild-data
Yum repo and related config files of %{distname}.

This package contains mock.cfg file.


%prep
%setup -T -c %{name}-%{version}
cp %{SOURCE0} ./
{% for arch in repo.archs -%}
cp %{SOURCE{{ loop.index }}} ./
{% endfor -%}
{% if keyid is defined and keyid != false %}cp %{SOURCE100} ./{% endif %}

%build


%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/etc/yum.repos.d
mkdir -p $RPM_BUILD_ROOT/etc/mock
install -m 644 {{ repo.reponame }}.repo $RPM_BUILD_ROOT/etc/yum.repos.d
for f in %{distname}-*.cfg; do install -m 644 $f $RPM_BUILD_ROOT/etc/mock; done
{% if keyid is defined and keyid != false %}mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/pki/rpm-gpg
for f in RPM-GPG-KEY-*; do install -m 644 $f $RPM_BUILD_ROOT%{_sysconfdir}/pki/rpm-gpg; done{% endif %}

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%config %{_sysconfdir}/yum.repos.d/*.repo
{% if keyid is defined and keyid != false %}%{_sysconfdir}/pki/rpm-gpg/RPM-GPG-KEY-*{% endif %}

%files -n       %{distname}-mockbuild-data
%defattr(-,root,root,-)
%config %{_sysconfdir}/mock/*.cfg


%changelog
* {{ datestamp }} {{ fullname }} <{{ email }}> - {{ repo.version }}-1
- Initial packaging.
