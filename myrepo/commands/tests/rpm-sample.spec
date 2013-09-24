Name:           rpm-sample
Version:        1.0
Release:        1%{?dist}
Summary:        Sample RPM package
Group:          System Environment/Base
License:        MIT
URL:            http://example.com
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
Source0:        README.sample


%description
Sample RPM package


%prep
%setup -T -c -n %{name}-%{version}
cp %{SOURCE0} ./


%build


%install


%clean


%files
%defattr(-,root,root,-)
%doc README.sample

%changelog
* Wed Sep 25 2013 John Doe <jdoe@example.com> - 1.0-1
- Initial packaging.
