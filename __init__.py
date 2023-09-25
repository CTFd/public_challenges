from CTFd.admin import config
from flask import render_template, request


from CTFd.models import Challenges
from CTFd.utils.dates import ctf_ended, ctf_paused, ctf_started
from CTFd.utils.user import authed
from CTFd.utils.helpers import get_errors, get_infos
from CTFd.utils.decorators import (
    require_verified_emails,
    during_ctf_time_only,
    ratelimit,
)
from CTFd.api.v1.challenges import ChallengeAttempt
from CTFd.plugins.challenges import get_chal_class
from CTFd.challenges import listing

from CTFd.utils.decorators.visibility import (
    check_challenge_visibility,
)


class ChallengeAttemptAnonymous(ChallengeAttempt):
    @ratelimit(method="POST", limit=10, interval=60)
    def post(self):
        if authed() is False:
            if request.content_type != "application/json":
                request_data = request.form
            else:
                request_data = request.get_json()

            challenge_id = request_data.get("challenge_id")

            challenge = Challenges.query.filter_by(id=challenge_id).first_or_404()
            chal_class = get_chal_class(challenge.type)
            status, message = chal_class.attempt(challenge, request)

            return {
                "success": True,
                "data": {
                    "status": "correct" if status else "incorrect",
                    "message": message,
                },
            }

        else:
            return super().post()


@during_ctf_time_only
@require_verified_emails
@check_challenge_visibility
def listing():
    infos = get_infos()
    errors = get_errors()

    if ctf_started() is False:
        errors.append(f"{config.ctf_name()} has not started yet")

    if ctf_paused() is True:
        infos.append(f"{config.ctf_name()} is paused")

    if ctf_ended() is True:
        infos.append(f"{config.ctf_name()} has ended")

    return render_template("challenges.html", infos=infos, errors=errors)


def load(app):
    app.view_functions[
        "api.challenges_challenge_attempt"
    ] = ChallengeAttemptAnonymous.as_view("api.challenges_challenge_attempt")
    app.view_functions["challenges.listing"] = listing
