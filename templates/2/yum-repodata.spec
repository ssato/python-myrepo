Name:           {{ repo.dist }}-release
Version:        {{ version }}
Release:        1%{?dist}
Summary:        Yum .repo files for {{ repo.dist }}
Group:          System Environment/Base
License:        MIT
URL:            {{ repo.url }}
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
Requires:       yum
Source0:        {{ repo.dist }}.repo
Source1:        {{ repo.dist }}.cfg


%description
Yum repo and related config files of {{ repo.dist }}.

This package contains .repo file.


%package -n     mock-data-{{ repo.dist }}
Summary:        Mock related config files for {{ repo.dist }}
Group:          Development/Tools
Requires:       mock


%description
Yum repo and related config files of {{ repo.dist }}.

This package contains mock.cfg file.


%prep
%setup -q -n %{name}-%{version}
cp %{SOURCE0} ./
cp %{SOURCE1} ./


%build


%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/etc/yum.repos.d
mkdir -p $RPM_BUILD_ROOT/etc/mock
install -m 644 {{ repo.dist }}.repo $RPM_BUILD_ROOT/etc/yum.repos.d
install -m 644 {{ repo.dist }}.cfg $RPM_BUILD_ROOT/etc/mock


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%{_sysconfdir}/yum.repos.d/*.repo


%files   -n     mock-data-{{ repo.dist }}
%defattr(-,root,root,-)
%{_sysconfdir}/mock/*.cfg


%changelog
* {{ datestamp }} {{ fullname }} <{{ email }}> - {{ version }}-1
- Initial packaging.
