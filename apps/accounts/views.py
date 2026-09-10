from datetime import timedelta
from django.core.cache import cache
from django.utils import timezone
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from apps.accounts.models import User


MAX_LOGIN_ATTEMPTS = 3
LOCKOUT_MINUTES = 10


class StyledAuthenticationForm(AuthenticationForm):
    role = forms.ChoiceField(
        choices=User.Role.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Login as',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['username'].label = 'Email'
        self.fields['password'].widget.attrs.update({'class': 'form-control'})

    def _client_ip(self):
        return self.request.META.get('REMOTE_ADDR') if self.request else None

    def _is_locked(self):
        ip = self._client_ip()
        if not ip:
            return None
        lock_until = cache.get(f'lockout:{ip}')
        if lock_until and timezone.now() < lock_until:
            return lock_until
        return None

    def _register_failure(self):
        ip = self._client_ip()
        if not ip:
            return None
        key = f'login_attempts:{ip}'
        attempts = cache.get(key, 0) + 1
        cache.set(key, attempts, timeout=LOCKOUT_MINUTES * 60)
        if attempts >= MAX_LOGIN_ATTEMPTS:
            lock_until = timezone.now() + timedelta(minutes=LOCKOUT_MINUTES)
            cache.set(f'lockout:{ip}', lock_until, timeout=LOCKOUT_MINUTES * 60)
            cache.delete(key)
            return ('locked', lock_until)
        return ('remaining', MAX_LOGIN_ATTEMPTS - attempts)

    def _clear_failures(self):
        ip = self._client_ip()
        if ip:
            cache.delete(f'login_attempts:{ip}')
            cache.delete(f'lockout:{ip}')

    def clean(self):
        lock_until = self._is_locked()
        if lock_until:
            minutes_left = max(1, int((lock_until - timezone.now()).total_seconds() // 60) + 1)
            raise forms.ValidationError(
                f"This device is locked due to too many failed login attempts. "
                f"Please try again in {minutes_left} minute(s)."
            )

        try:
            cleaned_data = super().clean()
        except forms.ValidationError:
            result = self._register_failure()
            if result and result[0] == 'locked':
                raise forms.ValidationError(
                    f"Too many failed login attempts (3/3). This device is now locked for {LOCKOUT_MINUTES} minutes."
                )
            elif result:
                raise forms.ValidationError(
                    f"Invalid email or password. You have {result[1]} attempt(s) left before this device is locked."
                )
            raise

        role = cleaned_data.get('role')
        if self.user_cache and role:
            if not self.user_cache.has_role(role):
                result = self._register_failure()
                if result and result[0] == 'locked':
                    raise forms.ValidationError(
                        f"Too many failed login attempts (3/3). This device is now locked for {LOCKOUT_MINUTES} minutes."
                    )
                elif result:
                    raise forms.ValidationError(
                        f"You are not assigned that role on this account. "
                        f"You have {result[1]} attempt(s) left before this device is locked."
                    )

        self._clear_failures()
        return cleaned_data


class CustomLoginView(LoginView):
    template_name = 'dashboard/landing.html'
    authentication_form = StyledAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.session['active_role'] = form.cleaned_data['role']
        response.set_cookie('returning_user', '1', max_age=60 * 60 * 24 * 365)
        return response

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

from apps.core.decorators import role_required
from apps.sis.models import Staff
from .forms import StaffInvitationForm, StaffOnboardingForm, generate_username
from .models import StaffInvitation


@login_required
@role_required('HEAD_OF_SCHOOL', 'ADMIN')
def staff_invite(request):
    if request.method == 'POST':
        form = StaffInvitationForm(request.POST)
        if form.is_valid():
            invitation = form.save()
            onboard_url = request.build_absolute_uri(
                reverse('accounts:staff_onboard', args=[invitation.token])
            )
            from django.core.mail import EmailMessage
            email_message = EmailMessage(
                subject='You are invited to join School App',
                body=(
                    f"Hello,\n\n"
                    f"You have been registered as {invitation.get_role_display()}"
                    f"{f' in the {invitation.department} department' if invitation.department else ''}.\n\n"
                    f"Please complete your profile using the link below:\n{onboard_url}\n\n"
                    f"This link expires in 7 days."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[invitation.email],
            )
            email_message.encoding = 'us-ascii'
            email_message.send()
            messages.success(request, f'Invitation sent to {invitation.email}.')
            return redirect('accounts:staff_invitations')
    else:
        form = StaffInvitationForm()
    return render(request, 'accounts/staff_invite.html', {'form': form})


@login_required
@role_required('HEAD_OF_SCHOOL', 'ADMIN')
def staff_invitations(request):
    invitations = StaffInvitation.objects.all().order_by('-created_at')
    return render(request, 'accounts/staff_invitations.html', {'invitations': invitations})


def staff_onboard(request, token):
    invitation = get_object_or_404(StaffInvitation, token=token)

    if not invitation.is_valid():
        return render(request, 'accounts/onboard_invalid.html', {'invitation': invitation})

    if request.method == 'POST':
        form = StaffOnboardingForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            username = generate_username(data['first_name'], data['last_name'])

            user = User(
                username=username,
                email=invitation.email,
                first_name=data['first_name'],
                last_name=data['last_name'],
                role=invitation.role,
                phone_number=data['phone_number'],
            )
            user.set_password(data['password1'])
            user.save()

            Staff.objects.create(
                user=user,
                department=invitation.department,
                gender=data['gender'],
                phone_number=data['phone_number'],
                address=data['address'],
                date_of_birth=data.get('date_of_birth'),
                photo=data.get('photo'),
            )

            invitation.is_used = True
            invitation.save()

            messages.success(request, 'Your profile is complete. You can now log in.')
            return redirect('accounts:login')
    else:
        form = StaffOnboardingForm()

    return render(request, 'accounts/staff_onboard.html', {'form': form, 'invitation': invitation})
