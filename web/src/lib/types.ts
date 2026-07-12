export interface Account {
	id: number;
	lunchflow_id: number | null;
	institution_name: string;
	name: string | null;
	currency: string;
	last_synced_at: string | null;
	round_up_since: string | null;
}

export interface AccountWithStats extends Account {
	unallocated_count: number;
	balance: string;
}

export interface Transaction {
	id: number;
	account_id: number;
	lunchflow_id: string | null;
	date: string | null;
	amount: string;
	currency: string;
	credit_debit_indicator: 'CRDT' | 'DBIT';
	status: 'booked' | 'pending' | 'opening_balance';
	merchant: string | null;
	description: string | null;
	note: string | null;
}

export interface Envelope {
	id: number;
	account_id: number;
	name: string;
	sort_order: number;
	created_at: string;
	// Optional parent group — null means the envelope sits at the account's top level
	group_id: number | null;
	// Goal columns — null means no goal is set
	goal_amount:     string | null;
	goal_rrule:      string | null;
	goal_dtstart:    string | null;
	goal_due_date:   string | null;
	goal_created_at: string | null;
}

export interface EnvelopeWithStats extends Envelope {
	allocated_raw:    number;
	allocated_total:  string;
	percent_of_total: number;
	// Net balance used for goal progress (CRDT allocations add, DBIT subtract)
	goal_balance:     number;
}

export type GroupTint = 'budget' | 'monthly' | 'savings' | 'fun';

export interface EnvelopeGroup {
	id: number;
	account_id: number;
	parent_id: number | null;
	name: string;
	tint: string;
	sort_order: number;
	created_at: string;
}

/** A node in the account's envelope tree: either a (recursively nested) group or a leaf envelope. */
export type EnvelopeTreeNode =
	| { kind: 'group'; group: EnvelopeGroup; children: EnvelopeTreeNode[] }
	| { kind: 'envelope'; envelope: EnvelopeWithStats };

export interface Split {
	id: number;
	transaction_id: number;
	amount: string;
	note: string | null;
	sort_order: number;
	is_round_up: boolean;
	is_default: boolean;
}

export interface SplitWithStatus extends Split {
	is_allocated: boolean;
	envelope_id: number | null;
	envelope_name: string | null;
}

export interface EnvelopeWithdrawal {
	id: number;
	from_envelope_id: number;
	from_envelope_name: string;
	to_envelope_id: number | null;
	amount: string;
	note: string | null;
	created_at: string;
}

export class SplitValidationError extends Error {
	constructor(message: string) {
		super(message);
		this.name = 'SplitValidationError';
	}
}

export class AlreadyAllocatedError extends Error {
	constructor(splitId: number) {
		super(`Split ${splitId} is already allocated`);
		this.name = 'AlreadyAllocatedError';
	}
}

export class WithdrawalAlreadyAllocatedError extends Error {
	constructor(withdrawalId: number) {
		super(`Withdrawal ${withdrawalId} is already allocated`);
		this.name = 'WithdrawalAlreadyAllocatedError';
	}
}

export class EnvelopeHasAllocationsError extends Error {
	constructor(envelopeId: number) {
		super(`Envelope ${envelopeId} has allocations and cannot be deleted`);
		this.name = 'EnvelopeHasAllocationsError';
	}
}

export class TransactionValidationError extends Error {
	constructor(message: string) {
		super(message);
		this.name = 'TransactionValidationError';
	}
}
