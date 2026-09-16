# v0.3.0
# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }

"""Splitbench v1 — native-GEN escrow with GenLayer jury adjudication.

...
"""
from datetime import datetime, timezone
import json
import genlayer as gl
from genlayer import *

@gl.evm.contract_interface
class _Recipient:
    class View:
        pass

    class Write:
        pass


class Splitbench(gl.Contract):
    jobs: TreeMap[str, str]
    milestones: TreeMap[str, str]
    job_ids: DynArray[str]
    next_job_nonce: u256

    def __init__(self):
        # Storage containers are provisioned by GenVM from their annotations;
        # unlike Python collections they must not be user-instantiated.
        self.next_job_nonce = u256(0)

    def _sender(self) -> str:
        return gl.message.sender_address.as_hex

    def _address_hex(self, value) -> str:
        """Normalize Studio's ABI-decoded address (int) or a native Address."""
        if isinstance(value, int):
            raw = format(value, "x")
            return Address("0x" + ("0" * 40 + raw)[-40:]).as_hex
        return value.as_hex

    def _same_address(self, stored: str, address: Address) -> bool:
        """Compare normalized hex; never serialize Address through str()."""
        return stored == address.as_hex

    def _key(self, job_id: str, mid: str) -> str:
        return job_id + ":" + mid

    def _load_job(self, job_id: str) -> dict:
        if job_id not in self.jobs:
            raise gl.vm.UserError("unknown job")
        return json.loads(self.jobs[job_id])

    def _load_milestone(self, job_id: str, mid: str) -> dict:
        key = self._key(job_id, mid)
        if key not in self.milestones:
            raise gl.vm.UserError("unknown milestone")
        return json.loads(self.milestones[key])

    def _save_job(self, job: dict) -> None:
        self.jobs[job["id"]] = json.dumps(job, sort_keys=True)

    def _save_milestone(self, milestone: dict) -> None:
        self.milestones[self._key(milestone["job_id"], milestone["mid"])] = json.dumps(milestone, sort_keys=True)

    def _require_party(self, job: dict) -> None:
        sender = gl.message.sender_address
        if not self._same_address(job["client"], sender) and not self._same_address(job["provider"], sender):
            raise gl.vm.UserError("only a job party")

    def _now(self) -> int:
        return int(datetime.now(timezone.utc).timestamp())

    def _transfer(self, recipient: str, amount: u256) -> None:
        if amount > u256(0):
            _Recipient(Address(recipient)).emit_transfer(value=amount)

    def _is_last_unfinalized(self, job: dict, current_mid: str) -> bool:
        for mid in job["milestone_ids"]:
            if mid != current_mid and self._load_milestone(job["id"], mid)["status"] != "FINAL":
                return False
        return True

    def _pay_milestone(self, job: dict, milestone: dict, provider_amount: u256) -> None:
        total = u256(int(job["total"]))
        weight = u256(int(milestone["weight_bps"]))
        normal_slice = total * weight // u256(10000)
        client_amount = normal_slice - provider_amount
        if self._is_last_unfinalized(job, milestone["mid"]):
            client_amount = total - u256(int(job["paid_provider"])) - u256(int(job["paid_client"])) - provider_amount
        self._transfer(job["provider"], provider_amount)
        self._transfer(job["client"], client_amount)
        job["paid_provider"] = int(u256(int(job["paid_provider"])) + provider_amount)
        job["paid_client"] = int(u256(int(job["paid_client"])) + client_amount)
        milestone["status"] = "FINAL"
        self._save_milestone(milestone)
        if self._is_last_unfinalized(job, ""):
            job["status"] = "CLOSED"
        self._save_job(job)

    @gl.public.write.payable
    def open(self, mode: str, provider: Address, brief: str, milestones_json: str,
             deadline_ts: u256, partial_enabled: bool, client_agent_id: str = "",
             provider_agent_id: str = "") -> str:
        if mode != "HUMAN" and mode != "AGENT":
            raise gl.vm.UserError("mode must be HUMAN or AGENT")
        if gl.message.value == u256(0):
            raise gl.vm.UserError("send GEN escrow value")
        if mode == "AGENT" and (client_agent_id == "" or provider_agent_id == ""):
            raise gl.vm.UserError("AGENT jobs require both agent ids")
        rows = json.loads(milestones_json)
        if not isinstance(rows, list) or len(rows) == 0:
            raise gl.vm.UserError("milestones_json must be a non-empty list")
        weights = 0
        seen = []
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("mid"), str) or row["mid"] == "":
                raise gl.vm.UserError("each milestone needs a non-empty mid")
            if row["mid"] in seen:
                raise gl.vm.UserError("milestone mids must be unique")
            seen.append(row["mid"])
            weights += int(row.get("weight_bps", -1))
            if int(row.get("weight_bps", -1)) <= 0:
                raise gl.vm.UserError("milestone weight must be positive")
            if not isinstance(row.get("spec"), str) or not isinstance(row.get("evidence_schema"), str):
                raise gl.vm.UserError("milestone needs spec and evidence_schema strings")
        if weights != 10000:
            raise gl.vm.UserError("milestone weights must sum to 10000")
        job_id = "job-" + str(self.next_job_nonce)
        self.next_job_nonce = self.next_job_nonce + u256(1)
        job = {"id": job_id, "mode": mode, "creator": self._sender(), "client": self._sender(),
               "provider": self._address_hex(provider), "client_agent_id": client_agent_id,
               "provider_agent_id": provider_agent_id, "client_card_snapshot": "",
               "provider_card_snapshot": "", "a2a_task_id": "", "brief": brief,
               "total": int(gl.message.value), "deadline_ts": int(deadline_ts),
               "partial_enabled": partial_enabled, "status": "OPEN", "milestone_ids": seen,
               "mutual_close_proposed_by": "", "mutual_close_bps": 0,
               "paid_provider": 0, "paid_client": 0}
        self._save_job(job)
        self.job_ids.append(job_id)
        for row in rows:
            milestone = {"job_id": job_id, "mid": row["mid"], "weight_bps": int(row["weight_bps"]),
                         "spec": row["spec"], "evidence_schema": row["evidence_schema"],
                         "submitted_uris": "[]", "status": "LOCKED", "verdict": "",
                         "awarded_bps": 0, "reason": "", "last_adjudicate_note": "",
                         "last_adjudicate_tx": ""}
            self._save_milestone(milestone)
        return job_id

    @gl.public.write
    def bind_a2a(self, job_id: str, task_id: str, client_card: str, provider_card: str) -> None:
        job = self._load_job(job_id)
        self._require_party(job)
        if job["mode"] != "AGENT":
            raise gl.vm.UserError("bind_a2a is only for AGENT jobs")
        if task_id == "" or client_card == "" or provider_card == "":
            raise gl.vm.UserError("task id and both card snapshots are required")
        job["a2a_task_id"] = task_id
        job["client_card_snapshot"] = client_card
        job["provider_card_snapshot"] = provider_card
        job["status"] = "ACTIVE"
        self._save_job(job)

    @gl.public.write
    def submit(self, job_id: str, mid: str, uris_json: str) -> None:
        job = self._load_job(job_id)
        milestone = self._load_milestone(job_id, mid)
        if not self._same_address(job["provider"], gl.message.sender_address):
            raise gl.vm.UserError("only provider can submit")
        if job["mode"] == "AGENT" and job["a2a_task_id"] == "":
            raise gl.vm.UserError("AGENT job requires bind_a2a before submit")
        uris = json.loads(uris_json)
        if not isinstance(uris, list) or not all(isinstance(uri, str) for uri in uris):
            raise gl.vm.UserError("uris_json must be a JSON string list")
        if milestone["status"] != "LOCKED":
            raise gl.vm.UserError("milestone is not locked")
        milestone["submitted_uris"] = json.dumps(uris)
        milestone["status"] = "SUBMITTED"
        job["status"] = "ACTIVE"
        self._save_milestone(milestone)
        self._save_job(job)

    @gl.public.write
    def adjudicate(self, job_id: str, mid: str) -> None:
        job = self._load_job(job_id)
        milestone = self._load_milestone(job_id, mid)
        if milestone["status"] != "SUBMITTED":
            raise gl.vm.UserError("adjudicate requires SUBMITTED")
        brief = job["brief"]
        spec = milestone["spec"]
        schema = milestone["evidence_schema"]
        urls = json.loads(milestone["submitted_uris"])
        cap = int(milestone["weight_bps"])
        partial = bool(job["partial_enabled"])

        def jury():
            evidence = ""
            for url in urls:
                if url != "":
                    try:
                        response = gl.nondet.web.get(url)
                        evidence += "\nURL: " + url + "\n" + response.body.decode("utf-8")[:15000]
                    except Exception:
                        evidence += "\nURL_UNAVAILABLE: " + url
            prompt = """You are Splitbench, an escrow jury.
Master brief:\n%s
Milestone spec:\n%s
Partial awards allowed: %s
Maximum bps for this milestone: %s
Evidence schema:\n%s
Fetched evidence (truncated):\n%s

Return JSON only with keys verdict, awarded_bps, cap_bps, citations, reason.
cap_bps MUST equal %s. If evidence is missing or off-schema, verdict REFUND
and awarded_bps 0. If partial not allowed, only RELEASE or REFUND. Cite URLs used.""" % (
                brief, spec, "yes" if partial else "no", cap, schema, evidence, cap)
            return gl.nondet.exec_prompt(prompt, response_format="json")

        def valid(data: dict) -> bool:
            if not isinstance(data, dict) or data.get("verdict") not in ("RELEASE", "REFUND", "PARTIAL"):
                return False
            if not isinstance(data.get("awarded_bps"), int) or not isinstance(data.get("cap_bps"), int):
                return False
            if data["cap_bps"] != cap or data["awarded_bps"] < 0 or data["awarded_bps"] > cap:
                return False
            if not isinstance(data.get("citations"), list) or not all(isinstance(x, str) for x in data["citations"]):
                return False
            if not isinstance(data.get("reason"), str):
                return False
            if data["verdict"] == "RELEASE": return data["awarded_bps"] == cap
            if data["verdict"] == "REFUND": return data["awarded_bps"] == 0
            return partial and 0 < data["awarded_bps"] < cap

        def validator(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return) or not valid(leader_result.calldata):
                return False
            own = jury()
            if not valid(own):
                return False
            leader_nonzero = leader_result.calldata["awarded_bps"] > 0
            own_nonzero = own["awarded_bps"] > 0
            if leader_nonzero != own_nonzero:
                return False
            if partial and own["verdict"] != leader_result.calldata["verdict"]:
                return False
            return abs(own["awarded_bps"] - leader_result.calldata["awarded_bps"]) <= 500

        result = gl.vm.run_nondet_unsafe(jury, validator)
        milestone["verdict"] = result["verdict"]
        milestone["awarded_bps"] = result["awarded_bps"]
        milestone["reason"] = result["reason"]
        milestone["last_adjudicate_note"] = "Accepted by jury; wait for protocol finality before settlement."
        milestone["status"] = "PENDING"
        self._save_milestone(milestone)

    @gl.public.write
    def attest_finalized_adjudicate(self, job_id: str, mid: str, finalized_tx_id: str) -> None:
        """Testnet bridge: records a party's externally-verified final tx id."""
        job = self._load_job(job_id)
        milestone = self._load_milestone(job_id, mid)
        self._require_party(job)
        if milestone["status"] != "PENDING" or finalized_tx_id == "":
            raise gl.vm.UserError("pending milestone and non-empty final tx id required")
        milestone["last_adjudicate_tx"] = finalized_tx_id
        milestone["status"] = "ACCEPTED"
        self._save_milestone(milestone)

    @gl.public.write
    def settle(self, job_id: str, mid: str, finalized_tx_id: str) -> None:
        job = self._load_job(job_id)
        milestone = self._load_milestone(job_id, mid)
        if milestone["status"] != "ACCEPTED" or milestone["last_adjudicate_tx"] != finalized_tx_id:
            raise gl.vm.UserError("settle requires matching attested finalized adjudicate tx")
        amount = u256(int(job["total"])) * u256(int(milestone["awarded_bps"])) // u256(10000)
        self._pay_milestone(job, milestone, amount)

    @gl.public.write
    def timeout_refund(self, job_id: str, mid: str) -> None:
        job = self._load_job(job_id)
        milestone = self._load_milestone(job_id, mid)
        if self._now() <= int(job["deadline_ts"]):
            raise gl.vm.UserError("deadline has not passed")
        if milestone["status"] == "SUBMITTED" or milestone["status"] == "FINAL":
            raise gl.vm.UserError("submitted or final milestone cannot timeout refund")
        milestone["verdict"] = "REFUND"
        milestone["awarded_bps"] = 0
        milestone["reason"] = "deadline passed before submission"
        self._pay_milestone(job, milestone, u256(0))

    @gl.public.write
    def propose_mutual_close(self, job_id: str, provider_bps: u256) -> None:
        job = self._load_job(job_id)
        self._require_party(job)
        if provider_bps > u256(10000):
            raise gl.vm.UserError("provider_bps must be <= 10000")
        for mid in job["milestone_ids"]:
            if self._load_milestone(job_id, mid)["status"] == "FINAL":
                raise gl.vm.UserError("mutual close is only available before any settlement")
        job["mutual_close_proposed_by"] = self._sender()
        job["mutual_close_bps"] = int(provider_bps)
        self._save_job(job)

    @gl.public.write
    def confirm_mutual_close(self, job_id: str) -> None:
        job = self._load_job(job_id)
        self._require_party(job)
        if job["mutual_close_proposed_by"] == "" or self._same_address(job["mutual_close_proposed_by"], gl.message.sender_address):
            raise gl.vm.UserError("other party must confirm a proposal")
        total = u256(int(job["total"]))
        provider_amount = total * u256(int(job["mutual_close_bps"])) // u256(10000)
        self._transfer(job["provider"], provider_amount)
        self._transfer(job["client"], total - provider_amount)
        job["paid_provider"] = int(provider_amount)
        job["paid_client"] = int(total - provider_amount)
        job["status"] = "CLOSED"
        self._save_job(job)
        for mid in job["milestone_ids"]:
            milestone = self._load_milestone(job_id, mid)
            if milestone["status"] != "FINAL":
                milestone["status"] = "FINAL"
                milestone["reason"] = "closed by mutual agreement"
                self._save_milestone(milestone)

    @gl.public.view
    def get_job(self, job_id: str) -> str:
        """JSON record: public schemas cannot expose a bare Python dict."""
        if job_id not in self.jobs:
            raise gl.vm.UserError("unknown job")
        return self.jobs[job_id]

    @gl.public.view
    def get_milestone(self, job_id: str, mid: str) -> str:
        """JSON record: public schemas cannot expose a bare Python dict."""
        key = self._key(job_id, mid)
        if key not in self.milestones:
            raise gl.vm.UserError("unknown milestone")
        return self.milestones[key]

    @gl.public.view
    def list_job_ids(self) -> str:
        ids = []
        for job_id in self.job_ids:
            ids.append(job_id)
        return json.dumps(ids)

    @gl.public.view
    def preview_payout(self, job_id: str, mid: str) -> str:
        job = self._load_job(job_id)
        milestone = self._load_milestone(job_id, mid)
        provider = u256(int(job["total"])) * u256(int(milestone["awarded_bps"])) // u256(10000)
        slice_amount = u256(int(job["total"])) * u256(int(milestone["weight_bps"])) // u256(10000)
        return json.dumps({"provider": int(provider), "client": int(slice_amount - provider)})
