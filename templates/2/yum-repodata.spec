Name:           {{ repo.name }}-release
Version:        {{ repo.version }}
Release:        1%{?dist}
Summary:        Yum .repo files for {{ repo.dist }}
Group:          System Environment/Base
License:        MIT
URL:            {{ repo.baseurl }}/
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
Requires:       yum
# NOTE: .repo file does not depends on arch but mock.cfg does.
Source0:        {{ repo.dist }}.repo
{% for arch in repo.archs -%}
Source{{ loop.index }}:        {{ repo.dist }}-{{ arch }}.cfg
{% endfor %}

%description
Yum repo and related config files of {{ repo.dist }}.

This package contains release (.repo) file.


%package -n     mock-data-{{ repo.name }}
Summary:        Mock related config files for {{ repo.dist }}
Group:          Development/Tools
Requires:       mock


%description -n mock-data-{{ repo.name }}
Yum repo and related config files of {{ repo.dist }}.

This package contains mock.cfg file.


%prep
%setup -T -c %{name}-%{version}
cp %{SOURCE0} ./
{% for arch in repo.archs -%}
cp %{SOURCE{{ loop.index }}} ./
{% endfor %}

%build


%install
rm -rf $RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/etc/yum.repos.d
mkdir -p $RPM_BUILD_ROOT/etc/mock
install -m 644 {{ repo.dist }}.repo $RPM_BUILD_ROOT/etc/yum.repos.d
for f in {{ repo.dist }}-*.cfg; do install -m 644 $f $RPM_BUILD_ROOT/etc/mock; done


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%config %{_sysconfdir}/yum.repos.d/*.repo


%files   -n     mock-data-{{ repo.name }}
%defattr(-,root,root,-)
%config %{_sysconfdir}/mock/*.cfg


%changelog
* {{ datestamp }} {{ fullname }} <{{ email }}> - {{ repo.version }}-1
- Initial packaging.

