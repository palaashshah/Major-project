export type Question = {
    id: number;
    question: string;
    options: {
        label: string;
        points: number;
    }[];
};

export const questions: Question[] = [
    {
        id: 4,
        question: "How many years until you plan on withdrawing regular income or a lump sum from this account?",
        options: [
            { label: "0 - 4 Years", points: 3 },
            { label: "5 - 10 Years", points: 6 },
            { label: "11 - 20 Years", points: 9 }
        ]
    },
    {
        id: 5,
        question: "What is your primary financial objective?",
        options: [
            { label: "Preserving capital and generating steady income", points: 3 },
            { label: "A balance of income and moderate growth", points: 6 },
            { label: "Maximum long-term capital growth", points: 9 }
        ]
    },
    {
        id: 6,
        question: "If the stock market were to suffer a sudden decline of 20% over a 3-month period, what are you most likely to do with your account?",
        options: [
            { label: "Sell all of my stock investments and move into safe cash/fixed income", points: 0 },
            { label: "Sell some of my stocks to reduce risk", points: 3 },
            { label: "Do nothing and wait for recovery", points: 7 },
            { label: "Move more of my cash into stocks to buy at a lower price", points: 10 }
        ]
    },
    {
        id: 7,
        question: "Which of the following events do you fear the most regarding your investments?",
        options: [
            { label: "A loss of 10% of my principal value over a short period (6 months or less)", points: 3 },
            { label: "Consistently underperforming broad market benchmarks", points: 9 },
            { label: "Missing out on an opportunity that would have yielded substantially higher long-term returns, despite having higher risk", points: 15 }
        ]
    },
    {
        id: 8,
        question: "How much short-term investment risk are you willing to take in order to achieve larger long-term investment returns?",
        options: [
            { label: "I am not willing to take any risk", points: 0 },
            { label: "I am willing to take a small amount of risk", points: 4 },
            { label: "I am willing to take a moderate amount of risk", points: 8 },
            { label: "I am willing to take as much risk as needed for maximum returns", points: 13 }
        ]
    },
    {
        id: 9,
        question: "What is your overall knowledge and experience with financial markets?",
        options: [
            { label: "None / Very little experience", points: 3 },
            { label: "Moderate / Some investment experience", points: 9 },
            { label: "High / Extensive experience", points: 12 }
        ]
    },
    {
        id: 10,
        question: "What is the maximum loss in any one-year period you would accept before changing your investments?",
        options: [
            { label: "Less than 5%", points: 2 },
            { label: "5% - 10%", points: 4 },
            { label: "11% - 20%", points: 7 },
            { label: "More than 20%", points: 10 }
        ]
    },
    {
        id: 11,
        question: "What is your average annual return expectation from this investment?",
        options: [
            { label: "0% - 3% (capital preservation)", points: 2 },
            { label: "3% - 5% (steady income)", points: 4 },
            { label: "5% - 7% (moderate growth)", points: 7 },
            { label: "More than 7% (aggressive growth)", points: 10 }
        ]
    },
    {
        id: 12,
        question: "Which best describes your overall investment approach?",
        options: [
            { label: "Prefers relative stability, minimal fluctuation", points: 3 },
            { label: "Prefers some growth, accepts occasional small losses", points: 5 },
            { label: "Prefers strong growth, accepts moderate losses", points: 7 },
            { label: "Prefers maximum returns, accepts significant losses", points: 9 }
        ]
    },
    {
        id: 13,
        question: "Do you have an emergency fund (savings of at least three months’ after-tax income)?",
        options: [
            { label: "I do not have an emergency fund", points: 0 },
            { label: "Yes, but less than 3 months", points: 3 },
            { label: "Yes, about 3 months", points: 6 },
            { label: "Yes, about 6 months", points: 9 },
            { label: "Yes, more than 6 months", points: 12 }
        ]
    }

];