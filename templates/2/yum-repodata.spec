Name:           {{ repo.name }}-release
Version:        {{ version }}
Release:        1%{?dist}
Summary:        Yum .repo files for {{ repo.name }}
Group:          System Environment/Base
License:        MIT
URL:            {{ repo.url }}
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
Requires:       yum
Source0:        repofile.basename
Source1:        mockcfg.basename


%description
Yum repo and related config files of {{ repo.name }}.

This package contains .repo file.


%package -n     mock-data-%{repo.name}
Summary:        Mock related config files for {{ repo.name }}
Group:          Development/Tools
Requires:       mock


%prep
%setup -q -n %{name}-%{version}
cp %{SOURCE0} ./
cp %{SOURCE1} ./


%build


%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/etc/yum.repos.d
mkdir -p $RPM_BUILD_ROOT/etc/mock
install -m 644 {{ repofile.basename }} $RPM_BUILD_ROOT/etc/yum.repos.d
install -m 644 {{ mockcfg.basename }} $RPM_BUILD_ROOT/etc/mock


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%{_sysconfdir}/yum.repos.d/*.repo


%files   -n     mock-data-%{repo.name}
%defattr(-,root,root,-)
%{_sysconfdir}/mock/*.cfg


%changelog
* {{ datestamp }} Satoru SATOH <ssato@redhat.com> - {{ version }}-1
- Initial packaging.
