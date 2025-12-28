/**
 * Reference Parser - Detect and parse legal section references in text
 *
 * Supports patterns:
 * - "section 922" or "section 922(a)(3)"
 * - "§922" or "§922(g)(1)"
 * - "18 U.S.C. 921(a)"
 * - "paragraph (3)" (contextual - requires current section)
 */

export interface ParsedReference {
	targetSection: string; // e.g., "922", "921"
	targetSubsection?: string; // e.g., "a", "g"
	targetSubdivisions?: string[]; // e.g., ["3"], ["1"]
	targetTitle?: string; // e.g., "18" (for cross-title references)
	text: string; // Original matched text
	fullProvisionId?: string; // Computed provision ID (e.g., "/us/usc/t18/s922/a/3")
}

export interface TextSegment {
	type: 'text' | 'reference';
	content: string;
	reference?: ParsedReference;
}

/**
 * Parse provision text and identify section references.
 *
 * @param text - The provision text to parse
 * @param currentSection - Current section number for contextual references (e.g., "922")
 * @returns Array of text segments (plain text + references)
 */
export function parseReferences(text: string, currentSection?: string): TextSegment[] {
	const segments: TextSegment[] = [];
	let lastIndex = 0;

	// Combined regex pattern for all reference types
	// Priority order: explicit section references > symbols > contextual
	const referencePattern =
		/(?:(\d+)\s+U\.S\.C\.\s+)?(?:section|§)\s*(\d+)(?:\(([a-z])\))?(?:\((\d+)\))?(?:\(([A-Z])\))?|paragraph\s*\((\d+)\)/gi;

	let match: RegExpExecArray | null;

	while ((match = referencePattern.exec(text)) !== null) {
		// Add text before this match
		if (match.index > lastIndex) {
			segments.push({
				type: 'text',
				content: text.slice(lastIndex, match.index)
			});
		}

		// Parse the reference
		const reference = parseReferenceMatch(match, currentSection);

		if (reference) {
			segments.push({
				type: 'reference',
				content: match[0],
				reference
			});
		} else {
			// Failed to parse, treat as text
			segments.push({
				type: 'text',
				content: match[0]
			});
		}

		lastIndex = match.index + match[0].length;
	}

	// Add remaining text
	if (lastIndex < text.length) {
		segments.push({
			type: 'text',
			content: text.slice(lastIndex)
		});
	}

	return segments;
}

/**
 * Parse a regex match into a ParsedReference.
 */
function parseReferenceMatch(
	match: RegExpExecArray,
	currentSection?: string
): ParsedReference | null {
	const [fullMatch, title, section, subsection, paragraph1, clause, contextualParagraph] = match;

	// Handle contextual "paragraph (N)" reference
	if (contextualParagraph) {
		if (!currentSection) {
			// Can't resolve without context
			return null;
		}

		return {
			targetSection: currentSection,
			targetSubdivisions: [contextualParagraph],
			text: fullMatch,
			fullProvisionId: buildProvisionId('18', currentSection, undefined, [contextualParagraph])
		};
	}

	// Handle explicit section reference
	if (section) {
		const subdivisions: string[] = [];
		if (paragraph1) subdivisions.push(paragraph1);
		if (clause) subdivisions.push(clause);

		return {
			targetTitle: title, // May be undefined
			targetSection: section,
			targetSubsection: subsection,
			targetSubdivisions: subdivisions.length > 0 ? subdivisions : undefined,
			text: fullMatch,
			fullProvisionId: buildProvisionId(title || '18', section, subsection, subdivisions)
		};
	}

	return null;
}

/**
 * Build a full provision ID from parsed components.
 *
 * @param title - USC title (e.g., "18")
 * @param section - Section number (e.g., "922")
 * @param subsection - Subsection letter (e.g., "a")
 * @param subdivisions - Paragraph/clause numbers (e.g., ["3", "A"])
 * @returns Provision ID (e.g., "/us/usc/t18/s922/a/3")
 */
function buildProvisionId(
	title: string,
	section: string,
	subsection?: string,
	subdivisions?: string[]
): string {
	let id = `/us/usc/t${title}/s${section}`;

	if (subsection) {
		id += `/${subsection}`;
	}

	if (subdivisions && subdivisions.length > 0) {
		for (const div of subdivisions) {
			id += `/${div}`;
		}
	}

	return id;
}

/**
 * Extract provision ID from a parsed reference.
 * Returns null if reference cannot be resolved to a provision ID.
 */
export function getProvisionIdFromReference(
	reference: ParsedReference,
	currentYear: number = 2024
): { provisionId: string; year: number } | null {
	if (reference.fullProvisionId) {
		return {
			provisionId: reference.fullProvisionId,
			year: currentYear
		};
	}

	return null;
}

/**
 * Simple test to check if text contains any section references.
 */
export function hasReferences(text: string): boolean {
	const referencePattern = /(?:\d+\s+U\.S\.C\.\s+)?(?:section|§)\s*\d+|paragraph\s*\(\d+\)/i;
	return referencePattern.test(text);
}
